"""
Models Package - Database Models for LearnNova
"""

from extensions import db  # type: ignore[import]

# Import all models for easy access
from models.user import User  # type: ignore[attr-defined]
from models.course import Course, Chapter, Enrollment, Category  # type: ignore[attr-defined]
from models.test import Test, Question, Result  # type: ignore[attr-defined]
from models.timetable import Timetable, TimetableItem  # type: ignore[attr-defined]
from models.roadmap import Roadmap, Payment, Notification, Certificate  # type: ignore[attr-defined]

__all__ = [
    'db',
    'User',
    'Course',
    'Chapter',
    'Enrollment',
    'Category',
    'Test',
    'Question',
    'Result',
    'Timetable',
    'TimetableItem',
    'Roadmap',
    'Payment',
    'Notification',
    'Certificate'
]
