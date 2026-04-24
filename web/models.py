from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import os

# Initialize SQLAlchemy instance
# We don't attach it to the app here to avoid circular imports. It will be attached in the application factory.
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    User model for authentication and tying Fix8 sessions/projects to specific researchers.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Establish a relationship so a User can readily access their projects
    projects = db.relationship('Project', backref='owner', lazy=True)

class Project(db.Model):
    """
    Represents an ongoing or saved Fix8 analysis session.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    
    # Path to the raw trial file stored efficiently on the persistent cloud volume, bypassing SQL limits
    file_path = db.Column(db.String(500), nullable=False)
    
    # State flags tracking processing
    is_demo = db.Column(db.Boolean, default=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
