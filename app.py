"""
LearnNova - Main Flask Application
AI-Powered Learning & Career Guidance Platform
"""

import os
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import Config
from extensions import db, migrate, login_manager, jwt

def create_app(config_class=Config):
    """Application Factory Pattern"""
    # Get the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    app = Flask(__name__, 
                static_folder=base_dir,  # Serve static files from project root
                static_url_path='')       # Serve at root path (css/, js/, img/, lib/)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    
    # Configure CORS
    from flask_cors import CORS
    CORS(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'  # type: ignore[assignment]
    login_manager.login_message = 'Please log in to access this page.'
    
    # Register blueprints
    from routes.main import main as main_blueprint
    from routes.auth import auth as auth_blueprint
    from routes.courses import courses as courses_blueprint
    from routes.dashboard import dashboard as dashboard_blueprint
    from routes.tests import tests as tests_blueprint
    from routes.timetable import timetable as timetable_blueprint
    from routes.ai import ai as ai_blueprint
    from routes.teacher import teacher as teacher_blueprint
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(courses_blueprint)
    app.register_blueprint(dashboard_blueprint)
    app.register_blueprint(tests_blueprint)
    app.register_blueprint(timetable_blueprint)
    app.register_blueprint(ai_blueprint)
    app.register_blueprint(teacher_blueprint)
    
    # Register API blueprints
    from api.v1 import api_v1
    app.register_blueprint(api_v1)
    
    # Setup logging
    from logging_config import setup_logging
    setup_logging(app)
    
    # Initialize cache service
    from services.cache_service import cache_service
    cache_service.init_app(app)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'app': 'LearnNova'}), 200
    
    # API health check
    @app.route('/api/health')
    def api_health():
        return jsonify({'status': 'healthy', 'version': '1.0.0'}), 200
    
    # Serve static files from root directory (css, js, img, lib folders)
    @app.route('/<path:filename>')
    def serve_static(filename):
        from flask import send_from_directory
        # Only serve from allowed directories
        allowed_dirs = ['css', 'js', 'img', 'lib']
        if any(filename.startswith(d + '/') for d in allowed_dirs):
            return send_from_directory(base_dir, filename)
        return '', 404
    
    return app


# Import User model for login_manager
@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return db.session.get(User, int(user_id))


if __name__ == '__main__':
    app = create_app()
    # Note: The reloader is disabled to prevent infinite restart loops caused by 
    # log file changes. For development with auto-reload, consider using:
    # - Flask's --reload flag: flask --app app run --debug
    # - Or a external debugger like debugpy
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
