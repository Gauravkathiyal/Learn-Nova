"""
Logging Configuration
"""

import logging
import logging.handlers
import os


def setup_logging(app):
    """Configure application logging"""
    
    # Create logs directory
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Format
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # File handler - app.log
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/app.log', 
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # File handler - error.log
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/error.log',
        maxBytes=10485760,
        backupCount=10
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    app.logger.addHandler(error_handler)
    
    # Access handler
    access_handler = logging.handlers.RotatingFileHandler(
        'logs/access.log',
        maxBytes=10485760,
        backupCount=10
    )
    access_log = logging.getLogger('werkzeug')
    access_log.setLevel(logging.INFO)
    access_log.addHandler(access_handler)
    
    app.logger.info('LearnNova application startup')
