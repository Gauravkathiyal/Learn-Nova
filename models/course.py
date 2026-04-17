"""
Course Models - Course, Chapter, Enrollment
"""

from datetime import datetime
from extensions import db  # type: ignore[import]


class Category(db.Model):
    """Category model for course categories"""
    
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))  # category image
    icon_class = db.Column(db.String(50))  # font-awesome class
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Size variants for masonry grid
    size_class = db.Column(db.String(20), default='medium')  # big, tall, medium, small, wide
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_course_count(self):
        """Get count of courses in this category"""
        return Course.query.filter_by(category=self.name).count()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'image': self.image,
            'icon_class': self.icon_class,
            'size_class': self.size_class,
            'display_order': self.display_order,
            'course_count': self.get_course_count()
        }
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Course(db.Model):
    """Course model for courses available on the platform"""
    
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # References Category.name
    subcategory = db.Column(db.String(50))  # Physics, Chemistry, etc.
    level = db.Column(db.String(20))  # beginner, intermediate, advanced
    description = db.Column(db.Text)
    thumbnail = db.Column(db.String(255))
    duration_weeks = db.Column(db.Integer)
    price = db.Column(db.Float, default=0)
    is_free = db.Column(db.Boolean, default=True)
    is_published = db.Column(db.Boolean, default=False)
    
    # Instructor
    instructor_name = db.Column(db.String(100))
    instructor_qualification = db.Column(db.String(200))
    
    # Metadata
    syllabus = db.Column(db.Text)  # JSON syllabus
    rating = db.Column(db.Float, default=0)
    total_reviews = db.Column(db.Integer, default=0)
    total_students = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chapters = db.relationship('Chapter', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    tests = db.relationship('Test', backref='course', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'subcategory': self.subcategory,
            'level': self.level,
            'description': self.description,
            'thumbnail': self.thumbnail,
            'duration_weeks': self.duration_weeks,
            'price': self.price,
            'is_free': self.is_free,
            'instructor_name': self.instructor_name,
            'rating': self.rating,
            'total_reviews': self.total_reviews,
            'total_students': self.total_students,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Course {self.title}>'


class Chapter(db.Model):
    """Chapter model for course content"""
    
    __tablename__ = 'chapters'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    video_url = db.Column(db.String(500))
    document_url = db.Column(db.String(500))
    order_index = db.Column(db.Integer, default=0)
    duration_minutes = db.Column(db.Integer)
    is_free_preview = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'description': self.description,
            'video_url': self.video_url,
            'document_url': self.document_url,
            'order_index': self.order_index,
            'duration_minutes': self.duration_minutes,
            'is_free_preview': self.is_free_preview
        }
    
    def __repr__(self):
        return f'<Chapter {self.title}>'


class Enrollment(db.Model):
    """Enrollment model for user-course relationships"""
    
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    status = db.Column(db.String(20), default='active')  # active, completed, dropped
    progress_percent = db.Column(db.Integer, default=0)
    chapters_completed = db.Column(db.Integer, default=0)
    
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, refunded
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='unique_enrollment'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'status': self.status,
            'progress_percent': self.progress_percent,
            'chapters_completed': self.chapters_completed,
            'enrolled_at': self.enrolled_at.isoformat() if self.enrolled_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'payment_status': self.payment_status
        }
    
    def __repr__(self):
        return f'<Enrollment user={self.user_id} course={self.course_id}>'
