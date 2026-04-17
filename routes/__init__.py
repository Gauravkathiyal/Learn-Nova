"""
Routes Package - Web Blueprints
"""

from routes.main import main  # type: ignore[attr-defined]
from routes.auth import auth  # type: ignore[attr-defined]
from routes.courses import courses  # type: ignore[attr-defined]
from routes.dashboard import dashboard  # type: ignore[attr-defined]
from routes.tests import tests  # type: ignore[attr-defined]
from routes.timetable import timetable  # type: ignore[attr-defined]
from routes.ai import ai

__all__ = [
    'main',
    'auth',
    'courses',
    'dashboard',
    'tests',
    'timetable',
    'ai'
]
