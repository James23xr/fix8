from flask import Blueprint, send_from_directory, jsonify, current_app, request
import os
import json
import uuid
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from web.models import db, Project

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'static'), 'dashboard.html')

@dashboard_bp.route('/api/projects', methods=['GET'])
@login_required
def get_projects():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    
    # Generate an initial demo project dynamically for new users (Phase 1 legacy demo)
    if not projects:
        demo_project = Project(
            name="Fix8 Sample Reading Trial",
            file_path="demo_data/demo_trial.json",
            is_demo=True,
            user_id=current_user.id
        )
        db.session.add(demo_project)
        db.session.commit()
        projects = [demo_project]
        
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "is_demo": p.is_demo
    } for p in projects])

@dashboard_bp.route('/api/projects/<int:project_id>/load', methods=['POST'])
@login_required
def load_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if not project:
        return jsonify({"error": "Project not found"}), 404
        
    from web.routes.api import get_engine
    import pandas as pd
    
    engine = get_engine()
    
    if project.is_demo:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'demo_data', 'demo_trial.json')
    else:
        file_path = os.path.join(os.environ.get('STORAGE_PATH', ''), project.file_path)
        
    if not os.path.exists(file_path):
        return jsonify({"error": "Data file missing from storage volume."}), 404
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            trial_data = json.load(f)
            
        x_cord, y_cord, duration = [], [], []
        if 'fixations' not in trial_data.keys():
            for key in trial_data:
                x_cord.append(trial_data[key][0])
                y_cord.append(trial_data[key][1])
                duration.append(trial_data[key][2])
        else:
            for fixation in trial_data["fixations"]:
                x_cord.append(fixation[0])
                y_cord.append(fixation[1])
                duration.append(fixation[2])
                
        eye_events = pd.DataFrame({
            "x_cord": x_cord,
            "y_cord": y_cord,
            "duration": duration,
            "eye_event": "fixation"
        })
        
        engine.eye_events = eye_events
        engine.trial_path = file_path
        
        return jsonify({"message": f"Project {project.name} loaded successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/api/projects/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if not project.is_demo:
        storage_path = os.environ.get('STORAGE_PATH', os.path.join(os.path.dirname(__file__), '..', 'uploads'))
        file_path = os.path.join(storage_path, project.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "Project deleted"})

@dashboard_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if not (file.filename.endswith('.json') or file.filename.endswith('.asc')):
        return jsonify({"error": "Invalid file type. Only .json and .asc allowed."}), 400
        
    filename = secure_filename(file.filename)
    unique_filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}_{filename}"
    
    storage_path = os.environ.get('STORAGE_PATH', os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    os.makedirs(storage_path, exist_ok=True)
    
    save_path = os.path.join(storage_path, unique_filename)
    file.save(save_path)
    
    project = Project(
        name=filename,
        file_path=unique_filename,
        is_demo=False,
        user_id=current_user.id
    )
    db.session.add(project)
    db.session.commit()
    
    return jsonify({
        "message": "File uploaded successfully",
        "project": {
            "id": project.id,
            "name": project.name,
            "is_demo": project.is_demo
        }
    })
