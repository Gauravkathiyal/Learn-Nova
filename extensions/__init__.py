"""
Flask Extensions Configuration
"""

from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager: LoginManager = LoginManager()
jwt = JWTManager()
cors = CORS()
