"""
Auth Routes - Login, Register, Logout
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify  # type: ignore[import]
from flask_login import login_user, logout_user, login_required, current_user  # type: ignore[import]
from models.user import User  # type: ignore[attr-defined]
from extensions import db  # type: ignore[import]
import logging

auth = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    # Check if user is already logged in - redirect based on role
    if current_user.is_authenticated:
        if current_user.role in ['teacher', 'admin', 'instructor']:
            return redirect(url_for('teacher.dashboard'))
        return redirect(url_for('dashboard.index'))
    
    # Get the role from query parameter (for direct faculty link)
    default_role = request.args.get('role', 'student')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        login_role = request.form.get('login_role', 'student')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.update_last_login()
            logger.info(f"User {user.email} logged in successfully")
        
        if user and user.check_password(password):
            login_user(user)
            user.update_last_login()
            logger.info(f"User {user.email} logged in successfully")
            
            # Redirect based on role selection
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # If user selects faculty but is not a teacher, redirect to become teacher page
            if login_role == 'faculty' and user.role not in ['teacher', 'admin', 'instructor']:
                flash(f'Welcome {user.name}! You need to register as a faculty member first.', 'info')
                return redirect(url_for('teacher.become_teacher'))
            
            # Check user role and redirect accordingly
            if user.role in ['teacher', 'admin', 'instructor']:
                flash(f'Welcome back, {user.name}! You are logged in as {user.role.title()}.', 'success')
                return redirect(url_for('teacher.dashboard'))
            else:
                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password', 'danger')
            logger.warning(f"Failed login attempt for email: {email}")
    
    return render_template('login.html', default_role=default_role, role=default_role)


@auth.route('/faculty-login')
def faculty_login():
    """Direct faculty login page"""
    # Check if user is already logged in
    if current_user.is_authenticated:
        if current_user.role in ['teacher', 'admin', 'instructor']:
            return redirect(url_for('teacher.dashboard'))
        flash('You are logged in as a student. Logout to login as faculty.', 'info')
        return redirect(url_for('dashboard.index'))
    
    return render_template('login.html', default_role='faculty')


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        category = request.form.get('category')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('signup.html')
        
        # Create user
        user = User(name=name, email=email, category=category)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {user.email}")
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('signup.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        category = request.form.get('category')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('login.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('login.html')
        
        # Create user
        user = User(name=name, email=email, category=category)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {user.email}")
        
        # Send welcome email (async task)
        # from tasks.email_tasks import send_welcome_email
        # send_welcome_email.delay(user.id)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('login.html', register=True)


@auth.route('/register-faculty', methods=['GET', 'POST'])
def register_faculty_page():
    """Registration page for faculty/teachers"""
    if current_user.is_authenticated:
        if current_user.role in ['teacher', 'admin', 'instructor']:
            return redirect(url_for('teacher.dashboard'))
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        qualification = request.form.get('qualification')
        experience = request.form.get('experience')
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # If user exists, update their role to teacher
            existing_user.role = 'teacher'
            existing_user.instructor_qualification = qualification
            db.session.commit()
            logger.info(f"Existing user {email} promoted to faculty")
            flash('You have been registered as faculty! Please login.', 'success')
            return redirect(url_for('auth.login'))
        
        # Create new user as teacher
        user = User(name=name, email=email, role='teacher', instructor_qualification=qualification)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New faculty registered: {user.email}")
        
        flash('Faculty registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('teacher/register_faculty.html')


@auth.route('/register-faculty/submit', methods=['POST'])
def register_faculty_submit():
    """Handle faculty registration form submission"""
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    qualification = request.form.get('qualification')
    experience = request.form.get('experience')
    
    # Validate passwords match
    if password != confirm_password:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('auth.register_faculty_page'))
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        # If user exists, update their role to teacher
        existing_user.role = 'teacher'
        existing_user.instructor_qualification = qualification
        db.session.commit()
        logger.info(f"Existing user {email} promoted to faculty")
        flash('You have been registered as faculty! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    # Create new user as teacher
    user = User(name=name, email=email, role='teacher', instructor_qualification=qualification)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    logger.info(f"New faculty registered: {user.email}")
    
    flash('Faculty registration successful! Please login.', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/logout')
@login_required
def logout():
    """Logout"""
    logger.info(f"User {current_user.email} logged out")
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))


@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.phone = request.form.get('phone')
        current_user.category = request.form.get('category')
        current_user.target_exam = request.form.get('target_exam')
        current_user.study_hours_per_day = int(request.form.get('study_hours', 4))
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        logger.info(f"User {current_user.email} updated profile")
        
        return redirect(url_for('auth.profile'))
    
    return render_template('profile.html', user=current_user)


@auth.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change password"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('auth.profile'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Password changed successfully', 'success')
    logger.info(f"User {current_user.email} changed password")
    
    return redirect(url_for('auth.profile'))


# API endpoints for mobile app
@auth.route('/api/register', methods=['POST'])
def api_register():
    """API: Register new user"""
    data = request.get_json()
    
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    user = User(
        name=data.get('name'),
        email=data.get('email'),
        category=data.get('category')
    )
    user.set_password(data.get('password'))
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Registration successful'}), 201


@auth.route('/api/login', methods=['POST'])
def api_login():
    """API: Login user"""
    data = request.get_json()
    
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user or not user.check_password(data.get('password')):
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    from flask_jwt_extended import create_access_token  # type: ignore[import]
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'success': True,
        'access_token': access_token,
        'user': user.to_dict()
    }), 200
