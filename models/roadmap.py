"""
Additional Models - Roadmap, Payment, Notification, Certificate
"""

from datetime import datetime
from extensions import db  # type: ignore[import]


class Roadmap(db.Model):
    """Roadmap model for AI-generated study roadmaps"""
    
    __tablename__ = 'roadmaps'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exam_name = db.Column(db.String(100))
    
    current_level = db.Column(db.String(20))  # beginner, intermediate, advanced
    target_date = db.Column(db.Date)
    
    # Roadmap data in JSON format
    roadmap_data = db.Column(db.Text)  # JSON with milestones
    
    milestones_completed = db.Column(db.Integer, default=0)
    total_milestones = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'exam_name': self.exam_name,
            'current_level': self.current_level,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'milestones_completed': self.milestones_completed,
            'total_milestones': self.total_milestones,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Roadmap {self.exam_name}>'


class Payment(db.Model):
    """Payment model for tracking payments"""
    
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    
    amount = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='INR')
    
    payment_method = db.Column(db.String(50))  # razorpay, stripe, upi
    transaction_id = db.Column(db.String(100), unique=True)
    
    status = db.Column(db.String(20), default='pending')  # pending, success, failed, refunded
    
    invoice_url = db.Column(db.String(500))
    payment_details = db.Column(db.Text)  # JSON with payment details
    
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'status': self.status,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Payment {self.transaction_id}>'


class Notification(db.Model):
    """Notification model for user notifications"""
    
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    notification_type = db.Column(db.String(20))  # info, success, warning, error
    
    is_read = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String(500))  # Link to relevant page
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def mark_as_read(self):
        self.is_read = True
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'action_url': self.action_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Notification {self.title}>'


class Certificate(db.Model):
    """Certificate model for course completion certificates"""
    
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    certificate_number = db.Column(db.String(50), unique=True)
    
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    download_url = db.Column(db.String(500))
    
    # Certificate details
    course_name = db.Column(db.String(200))
    user_name = db.Column(db.String(100))
    completion_date = db.Column(db.Date)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'certificate_number': self.certificate_number,
            'course_name': self.course_name,
            'user_name': self.user_name,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'download_url': self.download_url
        }
    
    def __repr__(self):
        return f'<Certificate {self.certificate_number}>'
