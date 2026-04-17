"""
User Model - Authentication & User Management
"""

from datetime import datetime
from flask_login import UserMixin  # type: ignore[import]
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager  # type: ignore[import]


class User(UserMixin, db.Model):
    """User model for authentication and profile management"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(15))
    profile_image = db.Column(db.String(255))
    
    # Plan & Subscription
    plan = db.Column(db.String(20), default='free')  # free, basic, premium
    
    # Study Preferences
    category = db.Column(db.String(50))  # JEE, NEET, UPSC, etc.
    target_exam = db.Column(db.String(100))
    exam_date = db.Column(db.Date)
    study_hours_per_day = db.Column(db.Integer, default=4)
    
    # Account Status
    role = db.Column(db.String(20), default='student')  # student, teacher, admin
    instructor_qualification = db.Column(db.String(255))  # For teachers/faculty
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Activity Tracking
    streak_days = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime)
    total_study_time = db.Column(db.Integer, default=0)  # in minutes
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    results = db.relationship('Result', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    timetables = db.relationship('Timetable', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    roadmaps = db.relationship('Roadmap', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    certificates = db.relationship('Certificate', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def increment_streak(self):
        """Increment study streak"""
        self.streak_days += 1
        db.session.commit()
    
    def reset_streak(self):
        """Reset study streak"""
        self.streak_days = 0
        db.session.commit()
    
    def add_study_time(self, minutes):
        """Add study time"""
        self.total_study_time += minutes
        db.session.commit()
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'profile_image': self.profile_image,
            'plan': self.plan,
            'category': self.category,
            'target_exam': self.target_exam,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'study_hours_per_day': self.study_hours_per_day,
            'streak_days': self.streak_days,
            'total_study_time': self.total_study_time,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
