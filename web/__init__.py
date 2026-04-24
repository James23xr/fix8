import os
from flask import Flask
from flask_session import Session
from web.models import db
from web.routes.api import api_bp

def create_app():
    """
    Application Factory for the Fix8 Web Server.
    Integrates Blueprints, Database bindings, and Server-side sessions.
    """
    app = Flask(__name__, static_folder='static', static_url_path='')

    # Dynamic Secrets & Render Postgres Deployment
    database_url = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(__file__), 'fix8.db')}")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-fix8-key-for-dev')
    
    # Configure server-side session
    app.config['SESSION_TYPE'] = 'filesystem'
    volume_path = os.environ.get('STORAGE_PATH', os.path.dirname(__file__))
    app.config['SESSION_FILE_DIR'] = os.path.join(volume_path, '.flask_sessions')
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

    # Initialize Plugins
    db.init_app(app)
    Session(app)
    
    from flask_login import LoginManager
    from web.models import User
    
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
    from flask_login import current_user
    from flask import redirect, url_for
    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return app.send_static_file('index.html')

    # Register API Blueprint
    app.register_blueprint(api_bp)
    
    from web.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from web.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    return app
