from flask import Blueprint, jsonify, request, session
import os
import json
import pandas as pd
import uuid
from src.core import Fix8Core

api_bp = Blueprint('api', __name__, url_prefix='/api')

ACTIVE_SESSIONS = {}

def get_engine():
    """Retrieve or create the Fix8Core engine for the current session."""
    if 'uid' not in session:
        session['uid'] = str(uuid.uuid4())
        
    uid = session['uid']
    if uid not in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS[uid] = Fix8Core()
        print(f"[*] Initialized new Fix8Core engine for session: {uid}")
        
    return ACTIVE_SESSIONS[uid]

def _get_state_payload(engine):
    payload = {
        "has_data": engine.eye_events is not None and not engine.eye_events.empty,
        "current_fixation": engine.current_fixation,
        "fixations": [],
        "saccades": [],
        "image_url": getattr(engine, 'image_url', None)
    }
    
    if payload["has_data"]:
        fix_df = engine.eye_events[engine.eye_events['eye_event'] == 'fixation']
        cols = ['x_cord', 'y_cord', 'duration']
        payload["fixations"] = fix_df[cols].to_dict(orient='records')
        
    return payload

@api_bp.route('/state', methods=['GET'])
def api_state():
    engine = get_engine()
    return jsonify(_get_state_payload(engine))

@api_bp.route('/load_demo', methods=['POST'])
def api_load_demo():
    engine = get_engine()
    demo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'demo_data', 'demo_trial.json')
    
    if not os.path.exists(demo_path):
        return jsonify({"error": f"Demo file not found at {demo_path}"}), 404
        
    try:
        with open(demo_path, 'r', encoding='utf-8') as f:
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
                
        engine.eye_events = pd.DataFrame({
            "x_cord": x_cord,
            "y_cord": y_cord,
            "duration": duration,
            "eye_event": "fixation"
        })
        engine.trial_path = demo_path
        engine.image_url = "/static/demo_data/demo_image.png"
        
        return jsonify({
            "message": "Demo data loaded",
            "fixation_count": len(engine.eye_events),
            "state": _get_state_payload(engine)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/action/move', methods=['POST'])
def api_action_move():
    direction = (request.json or {}).get('direction')
    engine = get_engine()
    if direction in ['right', 'next']:
        engine.next_fixation()
    elif direction in ['left', 'previous']:
        engine.previous_fixation()
    return jsonify({"message": f"Moved {direction}", "state": _get_state_payload(engine)})

@api_bp.route('/action/update_fixation', methods=['POST'])
def api_update_fixation():
    data = request.json or {}
    index, x, y = data.get('index'), data.get('x'), data.get('y')
    if None in (index, x, y):
        return jsonify({"error": "Missing fields"}), 400
    engine = get_engine()
    try:
        engine.update_fixation(int(index), float(x), float(y))
        return jsonify({"message": f"Updated {index}", "state": _get_state_payload(engine)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/distort/noise', methods=['POST'])
def api_distort_noise():
    threshold = int((request.json or {}).get('threshold', 5))
    engine = get_engine()
    if engine.eye_events is None or engine.eye_events.empty:
        return jsonify({"error": "No trial loaded"}), 400
    engine.apply_noise(threshold)
    return jsonify({"message": "Noise applied", "state": _get_state_payload(engine)})
