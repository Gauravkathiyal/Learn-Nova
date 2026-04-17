"""
Timetable Routes - AI Study Planner with Constraint-Based Scheduling
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request  # type: ignore[import]
from flask_login import login_required, current_user  # type: ignore[import]
from models import Timetable, TimetableItem  # type: ignore[attr-defined]
from models.course import Course  # type: ignore[import]
from extensions import db  # type: ignore[import]
from datetime import time
from routes.ml_study_planner import generate_ml_timetable

timetable = Blueprint('timetable', __name__)

# Course topics mapping for the timetable - organized by career goals
COURSE_TOPICS = {
    # Web Development
    'Web Development': [
        'HTML5 & CSS3 Fundamentals', 'JavaScript ES6+', 'DOM Manipulation', 
        'React.js Framework', 'Node.js & Express', 'RESTful API Design', 
        'Database (MongoDB/SQL)', 'Authentication & JWT', 'Git & Version Control', 'Deployment'
    ],
    # Data Science
    'Data Science': [
        'Python Programming', 'NumPy & Pandas', 'Data Visualization', 
        'Statistics & Probability', 'Machine Learning Basics', 'Scikit-Learn', 
        'Deep Learning Basics', 'NLP Fundamentals', 'Data Preprocessing', 'ML Projects'
    ],
    # Cyber Security
    'Cyber Security': [
        'Network Security Basics', 'Linux for Security', 'Python for Security', 
        'Ethical Hacking Intro', 'Penetration Testing', 'Web Application Security', 
        'Cryptography', 'Security Tools (Nmap, Metasploit)', 'Incident Response', 'Cyber Law'
    ],
    # Cloud Computing
    'Cloud Computing': [
        'Cloud Computing Intro', 'AWS Fundamentals', 'EC2 & S3', 
        'VPC & Networking', 'IAM & Security', 'Lambda & Serverless', 
        'Databases in Cloud', 'DevOps Basics', 'Containerization (Docker)', 'Cloud Projects'
    ],
    # Mobile Development
    'Mobile Development': [
        'Dart Programming', 'Flutter Basics', 'Widget & Layouts', 
        'State Management', 'REST APIs', 'Firebase Integration', 
        'Local Storage', 'Push Notifications', 'App Publishing', 'Flutter Advanced'
    ],
    # Machine Learning
    'Machine Learning': [
        'Python & Math Refresher', 'Linear Algebra', 'Statistics', 
        'Supervised Learning', 'Unsupervised Learning', 'Neural Networks', 
        'TensorFlow/PyTorch', 'Computer Vision', 'NLP Basics', 'ML Projects'
    ],
    # UPSC
    'UPSC': [
        'Indian History', 'World History', 'Geography (Physical)', 'Geography (Indian)', 
        'Polity & Constitution', 'Economy (Basic)', 'Economy (Current)', 
        'Science & Technology', 'Environment & Ecology', 'Current Affairs'
    ],
    # Competitive Exams
    'Competitive Exams': [
        'Quantitative Aptitude', 'Number Systems', 'Algebra', 
        'Geometry & Mensuration', 'Data Interpretation', 'Logical Reasoning', 
        'Verbal Reasoning', 'General Awareness', 'English Grammar', 'Mock Tests'
    ],
    # UI/UX Design
    'UI/UX Design': [
        'Design Thinking', 'Color Theory', 'Typography', 
        'Figma Essentials', 'Wireframing', 'Prototyping', 
        'User Research', 'Usability Testing', 'Design Systems', 'Portfolio Building'
    ],
    # Placement Preparation
    'Placement Prep': [
        'Aptitude - Quantitative', 'Aptitude - Logical', 'Aptitude - Verbal', 
        'DSA - Arrays & Strings', 'DSA - Linked Lists', 'DSA - Stacks & Queues', 
        'DSA - Trees & Graphs', 'System Design Basics', 'HR Interview Prep', 'Mock Interviews'
    ],
    # Legacy course names (for backward compatibility)
    'Full Stack Web Development Bootcamp': [
        'HTML & CSS Basics', 'JavaScript Fundamentals', 'React Development', 
        'Node.js & Express', 'Database Design', 'REST API Development', 
        'Authentication & Security', 'Deployment & DevOps'
    ],
    'Data Science & AI with Python': [
        'Python for Data Science', 'NumPy & Pandas', 'Data Visualization', 
        'Machine Learning Basics', 'Deep Learning', 'NLP Fundamentals', 
        'Model Deployment', 'AI Projects'
    ],
    'UPSC Prelims Complete Guide': [
        'History of India', 'Geography & Environment', 'Polity & Constitution', 
        'Economy & Budget', 'Current Affairs', 'Science & Technology', 
        'CSAT Reasoning', 'Answer Writing'
    ],
    'Machine Learning & Deep Learning': [
        'ML Fundamentals', 'Supervised Learning', 'Unsupervised Learning', 
        'Neural Networks', 'CNN & Computer Vision', 'RNN & NLP', 
        'Model Optimization', 'ML Projects'
    ],
    'Cyber Security Fundamentals': [
        'Network Security Basics', 'Ethical Hacking Intro', 'Penetration Testing', 
        'Security Tools', 'Incident Response', 'Cryptography', 
        'Web Security', 'Cyber Law'
    ],
    'Mobile App Development (Flutter)': [
        'Flutter Basics', 'Dart Programming', 'Widget Development', 
        'State Management', 'API Integration', 'Firebase Setup', 
        'App Publishing', 'Flutter Advanced'
    ],
    'AWS Cloud Practitioner Certification': [
        'AWS Cloud Overview', 'Compute Services', 'Storage & Database', 
        'Networking', 'Security in AWS', 'Pricing & Billing', 
        'Architecture Best Practices', 'Hands-on Labs'
    ],
    'UI/UX Design Masterclass': [
        'Design Principles', 'Color Theory', 'Typography', 
        'Figma Basics', 'Wireframing', 'Prototyping', 
        'User Research', 'Portfolio Building'
    ]
}


@timetable.route('/timetable')
def index():
    """Timetable page"""
    # Check if user is logged in
    from flask_login import current_user
    
    # Get the selected goal from URL parameter (if user just selected one)
    selected_goal = request.args.get('goal')
    
    if current_user.is_authenticated:
        active_timetable = Timetable.query.filter_by(
            user_id=current_user.id, 
            is_active=True
        ).first()
        
        # If user has an active timetable, use its target_exam for topics
        if active_timetable and active_timetable.target_exam and not selected_goal:
            selected_goal = active_timetable.target_exam
    else:
        active_timetable = None
    
    # Get career goals list
    career_goals = list(COURSE_TOPICS.keys())
    
    # Get topics for the selected goal (or first goal as default)
    if selected_goal and selected_goal in COURSE_TOPICS:
        goal_topics = COURSE_TOPICS[selected_goal]
    else:
        # Default to first career goal topics
        goal_topics = COURSE_TOPICS.get(career_goals[0], []) if career_goals else []
    
    # Get all published courses for the dropdown
    courses = Course.query.filter_by(is_published=True).all()
    
    return render_template('timetable.html', 
                          timetable=active_timetable, 
                          courses=courses, 
                          career_goals=career_goals,
                          goal_topics=goal_topics,
                          selected_goal=selected_goal)


@timetable.route('/timetable/generate', methods=['POST'])
@login_required
def generate():
    """Generate AI timetable with constraint-based scheduling"""
    study_hours = int(request.form.get('study_hours', 4))
    target_exam = request.form.get('target_exam', 'General Studies')
    exam_date = request.form.get('exam_date')
    
    # Parse difficulty weights from form
    difficulty_weights = {}
    for key, value in request.form.items():
        if key.startswith('difficulty_'):
            topic_name = key.replace('difficulty_', '')
            try:
                difficulty_weights[topic_name] = int(value)
            except ValueError:
                pass
    
    # Try constraint-based timetable generation
    ml_result = generate_ml_timetable(
        target_exam, 
        study_hours, 
        current_user.id,
        deadline=exam_date,
        difficulty_weights=difficulty_weights if difficulty_weights else None
    )
    
    if ml_result and ml_result.get('generated_by_ml', False):
        # Use constraint-based generated timetable
        timetable_items = ml_result.get('timetable_items', [])
        
        # Deactivate existing timetables
        Timetable.query.filter_by(user_id=current_user.id).update({'is_active': False})
        
        # Create new timetable
        timetable = Timetable(
            user_id=current_user.id,
            name=f'AI Study Plan - {target_exam}',
            study_hours_per_day=study_hours,
            target_exam=target_exam,
            generated_by_ai=True
        )
        
        db.session.add(timetable)
        db.session.commit()
        
        # Create timetable items from result
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for item_data in timetable_items:
            day_name = item_data.get('day', 'Monday')
            day_of_week = day_names.index(day_name) if day_name in day_names else 0
            
            start_str = item_data.get('start_time', '09:00')
            end_str = item_data.get('end_time', '10:30')
            
            # Convert string times to Python time objects
            start_time_obj = time(int(start_str.split(':')[0]), int(start_str.split(':')[1]))
            end_time_obj = time(int(end_str.split(':')[0]), int(end_str.split(':')[1]))
            
            item = TimetableItem(
                timetable_id=timetable.id,
                day_of_week=day_of_week,
                start_time=start_time_obj,
                end_time=end_time_obj,
                subject=item_data.get('subject', target_exam),
                topic=item_data.get('topic', 'Study Time'),
                is_completed=False
            )
            db.session.add(item)
        
        db.session.commit()
        
        # Build success message
        success_msg = f'Your personalized {target_exam} study timetable has been generated! {study_hours} hours/day with mock tests on weekends.'
        if exam_date:
            success_msg += f' Deadline: {exam_date}.'
        if difficulty_weights:
            success_msg += f' Custom difficulty weights applied to {len(difficulty_weights)} topics.'
        
        flash(success_msg, 'success')
    else:
        # Fall back to rule-based timetable generation
        # Get career goal specific topics from COURSE_TOPICS
        subjects = COURSE_TOPICS.get(target_exam, get_subjects_for_exam(target_exam))
        
        # Deactivate existing timetables
        Timetable.query.filter_by(user_id=current_user.id).update({'is_active': False})
        
        # Create new timetable
        timetable = Timetable(
            user_id=current_user.id,
            name=f'AI Study Plan - {target_exam}',
            study_hours_per_day=study_hours,
            target_exam=target_exam,
            generated_by_ai=True
        )
        
        db.session.add(timetable)
        db.session.commit()
        
        # Create timetable items for all 7 days
        # day_of_week: 0=Monday, 1=Tuesday, ..., 5=Saturday, 6=Sunday
        days = [0, 1, 2, 3, 4, 5, 6]
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Define time slots based on study hours
        # Each session is 1.5 hours with breaks between them
        time_slots = []
        start_hour = 9  # Start at 9 AM
        
        # Calculate slot duration and gap based on number of study hours
        # More hours = shorter gaps between sessions
        if study_hours <= 2:
            slot_duration = 90  # 1.5 hours
            gap = 60  # 1 hour break
        elif study_hours <= 4:
            slot_duration = 90  # 1.5 hours
            gap = 45  # 45 min break
        else:
            slot_duration = 75  # 1.25 hours  
            gap = 30  # 30 min break
        
        for i in range(study_hours):
            slot_start = start_hour + (i * (slot_duration + gap) // 60)
            end_hour = slot_start + (slot_duration // 60)
            end_min = slot_duration % 60
            if slot_start < 21:  # Don't go past 9 PM
                time_slots.append((f'{slot_start:02d}:00', f'{end_hour:02d}:{end_min:02d}' if end_min else f'{end_hour:02d}:00'))
        
        # Ensure at least one time slot
        if not time_slots:
            time_slots = [('09:00', '10:30')]
        
        # Get career goal specific topics
        goal_topics = COURSE_TOPICS.get(target_exam, get_subjects_for_exam(target_exam))
        
        # Generate items for each day
        topic_idx = 0
        for day_idx, day in enumerate(days):
            is_weekend = day in [5, 6]  # Saturday or Sunday
            
            # For weekends, add mock tests
            if is_weekend:
                # Add mock test session
                item = TimetableItem(
                    timetable_id=timetable.id,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(12, 0),
                    subject='Mock Test Series',
                    topic=f'Full Length Mock Test - {day_names[day]}',
                    is_completed=False
                )
                db.session.add(item)
                
                # Add test analysis
                item = TimetableItem(
                    timetable_id=timetable.id,
                    day_of_week=day,
                    start_time=time(14, 0),
                    end_time=time(16, 0),
                    subject='Test Analysis',
                    topic=f'Mock Test Analysis & Revision - {day_names[day]}',
                    is_completed=False
                )
                db.session.add(item)
            else:
                # Weekday: Add regular study sessions based on study hours and career goal topics
                for slot_idx, (start_str, end_str) in enumerate(time_slots):
                    topic = goal_topics[topic_idx % len(goal_topics)] if goal_topics else 'Study Time'
                    
                    # Convert string times to Python time objects
                    start_time_obj = time(int(start_str.split(':')[0]), int(start_str.split(':')[1]))
                    end_time_obj = time(int(end_str.split(':')[0]), int(end_str.split(':')[1]))
                    
                    item = TimetableItem(
                        timetable_id=timetable.id,
                        day_of_week=day,
                        start_time=start_time_obj,
                        end_time=end_time_obj,
                        subject=target_exam,
                        topic=topic,
                        is_completed=False
                    )
                    db.session.add(item)
                    topic_idx += 1
        
        db.session.commit()
        
        flash(f'Your personalized {target_exam} study timetable has been generated! {study_hours} hours/day with mock tests on weekends.', 'success')
    
    return redirect(url_for('timetable.index', goal=target_exam))


def get_subjects_for_exam(exam):
    """Get subjects based on target exam"""
    exam_subjects = {
        'UPSC': ['General Studies - Paper 1', 'Current Affairs', 'History', 'Geography', 'Polity', 'Economics', 'Science & Technology'],
        'SSC CGL': ['Quantitative Aptitude', 'English Comprehension', 'Reasoning', 'General Awareness'],
        'SSC': ['Quantitative Aptitude', 'English Comprehension', 'Reasoning', 'General Awareness'],
        'Railway': ['General Awareness', 'Mathematics', 'Reasoning', 'General Intelligence'],
        'Web Development': ['HTML & CSS', 'JavaScript', 'Responsive Design', 'Web Projects', 'Practice Arena'],
        'Advanced Python': ['Python Basics', 'OOP Concepts', 'Data Structures', 'Web Frameworks', 'Database'],
        'Data Science': ['Python', 'Statistics', 'Machine Learning', 'Data Visualization', 'Deep Learning'],
        'Placement Prep': ['Aptitude', 'Pre Placement Questions', 'DSA/Data Structures', 'Coding Practice', 'Interview Prep'],
        'DSA': ['Arrays', 'Linked Lists', 'Stacks & Queues', 'Trees', 'Graphs', 'Dynamic Programming'],
        'Pre Placement': ['Quantitative Aptitude', 'Logical Reasoning', 'Pre Placement Questions', 'DSA', 'Soft Skills'],
        'Custom': ['Subject 1', 'Subject 2', 'Subject 3', 'Subject 4', 'Practice', 'Revision'],
        'default': ['Core Subject', 'Practice Problems', 'DSA/Data Structures', 'Pre Placement Questions', 'Revision', 'Mock Test']
    }
    return exam_subjects.get(exam, exam_subjects['default'])


@timetable.route('/timetable/mark-complete/<int:item_id>')
@login_required
def mark_complete(item_id):
    """Mark a timetable item as completed"""
    item = TimetableItem.query.get_or_404(item_id)
    
    if item.timetable.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('timetable.index'))
    
    item.mark_completed()
    db.session.commit()
    
    # Add study time to user
    if item.start_time and item.end_time:
        from datetime import datetime, time
        if isinstance(item.start_time, time) and isinstance(item.end_time, time):
            start = datetime.combine(item.timetable.created_at.date(), item.start_time)
            end = datetime.combine(item.timetable.created_at.date(), item.end_time)
            minutes = (end - start).seconds // 60
            current_user.add_study_time(minutes)
    
    flash('Item marked as completed!', 'success')
    return redirect(url_for('timetable.index'))
