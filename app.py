from flask import Flask, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
from extensions import db, login_manager, migrate, mail
from config import Config

# Load environment variables
load_dotenv()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration from Config class
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # Enable CORS for React frontend
    CORS(app, origins=[os.getenv('FRONTEND_URL', 'http://localhost:3000')])
    
    # Configure login manager
    login_manager.login_message = 'Please log in to access this page.'
    
    # Import and register blueprints
    from auth import auth_bp
    from main import main_bp
    from api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Add static file serving for React build
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files from React build"""
        import os
        static_dir = os.path.join(os.getcwd(), 'frontend', 'build', 'static')
        return send_from_directory(static_dir, filename)
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app

# Configure login manager
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id)) 