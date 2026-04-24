from flask import Blueprint, request, jsonify, redirect, url_for, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
import os
from web.models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json or request.form
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session['uid'] = str(user.id)
            if request.is_json:
                return jsonify({"message": "Logged in successfully.", "redirect": "/"})
            return redirect(url_for('index'))
            
        if request.is_json:
            return jsonify({"error": "Invalid username or password"}), 401
        return "Invalid credentials", 401
        
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'static'), 'auth.html')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json or request.form
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400
        
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Username already exists"}), 400
        
    new_user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    
    login_user(new_user)
    session['uid'] = str(new_user.id)
    
    if request.is_json:
         return jsonify({"message": "User created", "redirect": "/"})
    return redirect(url_for('index'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('uid', None)
    return redirect(url_for('auth.login'))
