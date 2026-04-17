"""
API Package - REST API v1
"""

from flask import Blueprint  # type: ignore[import]

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

from api.v1 import auth, users, courses, tests  # type: ignore[import]

__all__ = ['api_v1']
