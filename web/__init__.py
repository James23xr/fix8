import os
from flask import Flask, session, send_from_directory, redirect, url_for
from flask_session import Session
from flask_login import LoginManager, current_user
from web.models import db, User
from web.routes.api import api_bp

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')

    # Dynamic Secrets & Render Postgres Deployment
    # Use standard environment variables, falling back to SQLite for local development
    database_url = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(__file__), 'fix8.db')}")
    # Fix Render Postgres SQLAlchemy dialect format (postgres:// to postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-fix8-key-for-dev')
    
    # Configure server-side session (optional but we will keep filesystem for now to hold non-SQL core logic)
    app.config['SESSION_TYPE'] = 'filesystem'
    # We want sessions to persist in Render's persistent disk volume if available, else local
    volume_path = os.environ.get('STORAGE_PATH', os.path.dirname(__file__))
    app.config['SESSION_FILE_DIR'] = os.path.join(volume_path, '.flask_sessions')
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

    # Initialize Plugins
    db.init_app(app)
    Session(app)
    
    # Setup LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialize DB tables
    with app.app_context():
        db.create_all()

    # Route: Static File Entrypoint
    @app.route('/')
    def index():
        # Require login for the visualizer
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return app.send_static_file('index.html')

    # Register Blueprints
    app.register_blueprint(api_bp)
    
    from web.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from web.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    return app
