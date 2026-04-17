"""
Timetable Models - Timetable and TimetableItem
"""

from datetime import datetime
from extensions import db  # type: ignore[import]


class Timetable(db.Model):
    """Timetable model for AI-generated study schedules"""
    
    __tablename__ = 'timetables'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), default='My Study Plan')
    
    # Schedule in JSON format
    schedule = db.Column(db.Text)  # JSON schedule
    
    is_active = db.Column(db.Boolean, default=True)
    generated_by_ai = db.Column(db.Boolean, default=False)
    
    # Study preferences used
    study_hours_per_day = db.Column(db.Integer, default=4)
    target_exam = db.Column(db.String(100))
    exam_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('TimetableItem', backref='timetable', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'is_active': self.is_active,
            'generated_by_ai': self.generated_by_ai,
            'study_hours_per_day': self.study_hours_per_day,
            'target_exam': self.target_exam,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Timetable {self.id} user={self.user_id}>'


class TimetableItem(db.Model):
    """TimetableItem model for individual schedule items"""
    
    __tablename__ = 'timetable_items'
    
    id = db.Column(db.Integer, primary_key=True)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetables.id'), nullable=False)
    
    day_of_week = db.Column(db.Integer)  # 0-6 (Monday-Sunday)
    date = db.Column(db.Date)  # Specific date
    
    subject = db.Column(db.String(100))
    topic = db.Column(db.String(200))
    
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    
    notes = db.Column(db.Text)
    
    def mark_completed(self):
        self.is_completed = True
        self.completed_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'timetable_id': self.timetable_id,
            'day_of_week': self.day_of_week,
            'date': self.date.isoformat() if self.date else None,
            'subject': self.subject,
            'topic': self.topic,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'notes': self.notes
        }
    
    def __repr__(self):
        return f'<TimetableItem {self.subject} - {self.topic}>'
