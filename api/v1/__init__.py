"""
API v1 Package
"""

from flask import Blueprint  # type: ignore[import]

v1 = Blueprint('v1', __name__)

from api.v1 import auth, users, courses, tests, timetable, recommendations  # type: ignore[import]

__all__ = ['v1', 'auth', 'users', 'courses', 'tests', 'timetable', 'recommendations']

# Export api_v1 for backward compatibility
api_v1 = v1
