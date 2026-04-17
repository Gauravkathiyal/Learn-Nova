"""
Test Models - Test, Question, Result
"""

from datetime import datetime
from extensions import db  # type: ignore[import]


class Test(db.Model):
    """Test model for quizzes and exams"""
    
    __tablename__ = 'tests'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Teacher who created the test
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # JEE, NEET, 
    difficulty = db.Column(db.String(20))  # easy, medium, hard
    
    duration_minutes = db.Column(db.Integer, default=60)
    total_marks = db.Column(db.Integer, default=100)
    passing_score = db.Column(db.Integer, default=50)  # Minimum score to pass
    negative_marking = db.Column(db.Float, default=0.25)
    
    is_published = db.Column(db.Boolean, default=False)
    is_practice = db.Column(db.Boolean, default=False)  # Practice test vs full test
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='test', lazy='dynamic', cascade='all, delete-orphan')
    results = db.relationship('Result', backref='test', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'created_by': self.created_by,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'difficulty': self.difficulty,
            'duration_minutes': self.duration_minutes,
            'total_marks': self.total_marks,
            'passing_score': self.passing_score,
            'negative_marking': self.negative_marking,
            'question_count': self.questions.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Test {self.title}>'


class Question(db.Model):
    """Question model for test questions"""
    
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='mcq')  # mcq, true_false, integer
    
    option1 = db.Column(db.String(500))
    option2 = db.Column(db.String(500))
    option3 = db.Column(db.String(500))
    option4 = db.Column(db.String(500))
    
    correct_answer = db.Column(db.String(10), nullable=False)  # 1, 2, 3, 4 or True/False
    explanation = db.Column(db.Text)
    
    marks = db.Column(db.Integer, default=4)
    negative_marks = db.Column(db.Float, default=1)
    order_index = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self, include_answer=False):
        data = {
            'id': self.id,
            'test_id': self.test_id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'option1': self.option1,
            'option2': self.option2,
            'option3': self.option3,
            'option4': self.option4,
            'marks': self.marks,
            'negative_marks': self.negative_marks,
            'order_index': self.order_index
        }
        if include_answer:
            data['correct_answer'] = self.correct_answer
            data['explanation'] = self.explanation
        return data
    
    def __repr__(self):
        return f'<Question {self.id}>'


class Result(db.Model):
    """Result model for user test attempts"""
    
    __tablename__ = 'results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    
    score = db.Column(db.Integer, default=0)
    total_marks = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Float, default=0)
    
    correct_answers = db.Column(db.Integer, default=0)
    wrong_answers = db.Column(db.Integer, default=0)
    unattempted = db.Column(db.Integer, default=0)
    
    rank = db.Column(db.Integer)  # All India Rank
    time_taken = db.Column(db.Integer)  # Time taken in seconds
    
    answers = db.Column(db.Text)  # JSON of user answers
    status = db.Column(db.String(20), default='completed')  # in_progress, completed, abandoned
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_percentage(self):
        if self.total_marks > 0:
            self.percentage = (self.score / self.total_marks) * 100
        return self.percentage
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'test_id': self.test_id,
            'score': self.score,
            'total_marks': self.total_marks,
            'percentage': round(self.percentage, 2),
            'correct_answers': self.correct_answers,
            'wrong_answers': self.wrong_answers,
            'unattempted': self.unattempted,
            'rank': self.rank,
            'time_taken': self.time_taken,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }
    
    def __repr__(self):
        return f'<Result user={self.user_id} test={self.test_id} score={self.score}>'
