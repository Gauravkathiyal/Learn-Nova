"""
Teacher Routes - Teacher Dashboard & Content Management
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify  # type: ignore[import]
from flask_login import login_required, current_user  # type: ignore[import]
from models import Course, Chapter, Enrollment, Test, Result, User  # type: ignore[attr-defined]
from extensions import db  # type: ignore[import]
from datetime import datetime

teacher = Blueprint('teacher', __name__)


def check_teacher_role():
    """Check if user is a teacher or admin"""
    return current_user.is_authenticated and (current_user.is_admin or getattr(current_user, 'role', 'student') in ['teacher', 'admin', 'instructor'])


@teacher.route('/teacher')
@teacher.route('/teacher/dashboard')
@login_required
def dashboard():
    """Teacher dashboard - shows stats and quick actions"""
    if not check_teacher_role():
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        # Get teacher's courses
        courses = Course.query.filter_by(instructor_name=current_user.name).all() if hasattr(Course, 'instructor_name') else []
    except Exception:
        courses = []
    
    # Get stats
    total_students = 0
    total_revenue = 0
    try:
        for course in courses:
            total_students += getattr(course, 'total_students', 0) or 0
            # Calculate revenue (simplified)
            total_revenue += (getattr(course, 'price', 0) or 0) * (getattr(course, 'total_students', 0) or 0)
    except Exception:
        pass
    
    # Get recent enrollments
    recent_enrollments = []
    try:
        for course in courses:
            enrollments = Enrollment.query.filter_by(course_id=course.id).order_by(Enrollment.enrolled_at.desc()).limit(5).all()
            recent_enrollments.extend(enrollments)
        recent_enrollments = sorted(recent_enrollments, key=lambda x: x.enrolled_at, reverse=True)[:5] if recent_enrollments else []
    except Exception:
        recent_enrollments = []
    
    return render_template('teacher/teacher_dashboard.html',
                          courses=courses or [],
                          total_students=total_students,
                          total_revenue=total_revenue,
                          recent_enrollments=recent_enrollments)


@teacher.route('/teacher/courses')
@login_required
def courses():
    """List all teacher's courses"""
    if not check_teacher_role():
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    courses = Course.query.filter_by(instructor_name=current_user.name).order_by(Course.created_at.desc()).all()
    return render_template('teacher/teacher_courses.html', courses=courses)


@teacher.route('/teacher/course/create', methods=['GET', 'POST'])
@login_required
def create_course():
    """Create a new course"""
    if not check_teacher_role():
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        level = request.form.get('level')
        description = request.form.get('description')
        price = float(request.form.get('price', 0))
        is_free = 'is_free' in request.form
        
        course = Course(
            title=title,
            category=category,
            subcategory=subcategory,
            level=level,
            description=description,
            price=price,
            is_free=is_free,
            instructor_name=current_user.name,
            is_published=False
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash(f'Course "{title}" created successfully!', 'success')
        return redirect(url_for('teacher.edit_course', course_id=course.id))
    
    return render_template('teacher/teacher_create_course.html')


@teacher.route('/teacher/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    """Edit an existing course"""
    if not check_teacher_role():
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    course = Course.query.get_or_404(course_id)
    
    # Check ownership
    if course.instructor_name != current_user.name and not current_user.is_admin:
        flash('You do not have permission to edit this course.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    if request.method == 'POST':
        course.title = request.form.get('title')
        course.category = request.form.get('category')
        course.subcategory = request.form.get('subcategory')
        course.level = request.form.get('level')
        course.description = request.form.get('description')
        course.price = float(request.form.get('price', 0))
        course.is_free = 'is_free' in request.form
        course.is_published = 'is_published' in request.form
        
        db.session.commit()
        
        flash(f'Course "{course.title}" updated successfully!', 'success')
        return redirect(url_for('teacher.courses'))
    
    return render_template('teacher/teacher_edit_course.html', course=course)


@teacher.route('/teacher/course/<int:course_id>/chapters', methods=['GET', 'POST'])
@login_required
def manage_chapters(course_id):
    """Manage course chapters"""
    if not check_teacher_role():
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    course = Course.query.get_or_404(course_id)
    
    # Check ownership
    if course.instructor_name != current_user.name and not current_user.is_admin:
        flash('You do not have permission to edit this course.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        video_url = request.form.get('video_url')
        document_url = request.form.get('document_url')
        duration_minutes = int(request.form.get('duration_minutes', 0))
        is_free_preview = 'is_free_preview' in request.form
        
        # Get next order index
        last_chapter = Chapter.query.filter_by(course_id=course_id).order_by(Chapter.order_index.desc()).first()
        order_index = (last_chapter.order_index + 1) if last_chapter else 0
        
        chapter = Chapter(
            course_id=course_id,
            title=title,
            description=description,
            video_url=video_url,
            document_url=document_url,
            duration_minutes=duration_minutes,
            is_free_preview=is_free_preview,
            order_index=order_index
        )
        
        db.session.add(chapter)
        db.session.commit()
        
        flash(f'Chapter "{title}" added successfully!', 'success')
        return redirect(url_for('teacher.manage_chapters', course_id=course_id))
    
    chapters = Chapter.query.filter_by(course_id=course_id).order_by(Chapter.order_index).all()
    return render_template('teacher/teacher_chapters.html', course=course, chapters=chapters)


@teacher.route('/teacher/course/<int:course_id>/chapter/<int:chapter_id>/delete', methods=['POST'])
@login_required
def delete_chapter(course_id, chapter_id):
    """Delete a chapter"""
    if not check_teacher_role():
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    chapter = Chapter.query.get_or_404(chapter_id)
    course = Course.query.get_or_404(course_id)
    
    # Check ownership
    if course.instructor_name != current_user.name and not current_user.is_admin:
        flash('You do not have permission to delete this chapter.', 'danger')
        return redirect(url_for('teacher.courses'))
    
    db.session.delete(chapter)
    db.session.commit()
    
    flash('Chapter deleted successfully!', 'success')
    return redirect(url_for('teacher.manage_chapters', course_id=course_id))


@teacher.route('/teacher/tests')
@login_required
def tests():
    """List all teacher's tests"""
    if not check_teacher_role():
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get tests created by teacher (based on courses they teach)
    courses = Course.query.filter_by(instructor_name=current_user.name).all()
    course_ids = [c.id for c in courses]
    tests = Test.query.filter(Test.course_id.in_(course_ids)).order_by(Test.created_at.desc()).all()
    
    return render_template('teacher/teacher_tests.html', tests=tests)


@teacher.route('/teacher/test/create', methods=['GET', 'POST'])
@login_required
def create_test():
    """Create a new test"""
    if not check_teacher_role():
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get teacher's courses
    courses = Course.query.filter_by(instructor_name=current_user.name).all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        course_id = request.form.get('course_id')
        duration_minutes = int(request.form.get('duration_minutes', 30))
        passing_score = int(request.form.get('passing_score', 50))
        
        test = Test(
            title=title,
            description=description,
            course_id=course_id,
            duration_minutes=duration_minutes,
            passing_score=passing_score,
            created_by=current_user.id,
            is_published=False
        )
        
        db.session.add(test)
        db.session.commit()
        
        flash(f'Test "{title}" created successfully!', 'success')
        return redirect(url_for('teacher.edit_test', test_id=test.id))
    
    return render_template('teacher/teacher_create_test.html', courses=courses)


@teacher.route('/teacher/test/<int:test_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_test(test_id):
    """Edit an existing test"""
    if not check_teacher_role():
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    test = Test.query.get_or_404(test_id)
    courses = Course.query.filter_by(instructor_name=current_user.name).all()
    
    if request.method == 'POST':
        test.title = request.form.get('title')
        test.description = request.form.get('description')
        test.course_id = request.form.get('course_id')
        test.duration_minutes = int(request.form.get('duration_minutes', 30))
        test.passing_score = int(request.form.get('passing_score', 50))
        test.is_published = 'is_published' in request.form
        
        db.session.commit()
        
        flash(f'Test "{test.title}" updated successfully!', 'success')
        return redirect(url_for('teacher.tests'))
    
    return render_template('teacher/teacher_edit_test.html', test=test, courses=courses)


@teacher.route('/teacher/students')
@login_required
def students():
    """View all students enrolled in teacher's courses"""
    if not check_teacher_role():
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get teacher's courses
    courses = Course.query.filter_by(instructor_name=current_user.name).all()
    course_ids = [c.id for c in courses]
    
    # Get enrollments
    enrollments = Enrollment.query.filter(Enrollment.course_id.in_(course_ids)).order_by(Enrollment.enrolled_at.desc()).all()
    
    # Get unique students
    student_ids = set(e.user_id for e in enrollments)
    students = User.query.filter(User.id.in_(student_ids)).all()
    
    return render_template('teacher/teacher_students.html', students=students, enrollments=enrollments, courses=courses)


@teacher.route('/teacher/student/<int:user_id>/progress')
@login_required
def student_progress(user_id):
    """View a specific student's progress"""
    if not check_teacher_role():
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    student = User.query.get_or_404(user_id)
    
    # Get teacher's courses
    courses = Course.query.filter_by(instructor_name=current_user.name).all()
    course_ids = [c.id for c in courses]
    
    # Get student's enrollments in teacher's courses
    enrollments = Enrollment.query.filter(
        Enrollment.user_id == user_id,
        Enrollment.course_id.in_(course_ids)
    ).all()
    
    # Get student's results
    results = Result.query.filter_by(user_id=user_id).all()
    
    return render_template('teacher/teacher_student_progress.html', 
                          student=student, 
                          enrollments=enrollments, 
                          results=results,
                          courses=courses)


@teacher.route('/teacher/analytics')
@login_required
def analytics():
    """View teaching analytics"""
    if not check_teacher_role():
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get teacher's courses
    courses = Course.query.filter_by(instructor_name=current_user.name).all()
    
    # Calculate stats
    total_students = sum(c.total_students for c in courses)
    total_courses = len(courses)
    total_revenue = sum(c.price * c.total_students for c in courses)
    
    # Get recent activity
    course_ids = [c.id for c in courses]
    recent_enrollments = Enrollment.query.filter(
        Enrollment.course_id.in_(course_ids)
    ).order_by(Enrollment.enrolled_at.desc()).limit(10).all()
    
    return render_template('teacher/teacher_analytics.html',
                          courses=courses,
                          total_students=total_students,
                          total_courses=total_courses,
                          total_revenue=total_revenue,
                          recent_enrollments=recent_enrollments)


@teacher.route('/become-teacher', methods=['GET', 'POST'])
@login_required
def become_teacher():
    """Request to become a teacher"""
    if current_user.role in ['teacher', 'admin', 'instructor']:
        return redirect(url_for('teacher.dashboard'))
    
    if request.method == 'POST':
        qualification = request.form.get('qualification')
        experience = request.form.get('experience')
        bio = request.form.get('bio')
        
        # Update user role to teacher
        current_user.role = 'teacher'
        
        # Store additional info (could be in a separate table)
        current_user.instructor_qualification = qualification
        
        db.session.commit()
        
        flash('Congratulations! You are now a teacher. You can access the teacher dashboard.', 'success')
        return redirect(url_for('teacher.dashboard'))
    
    return render_template('teacher/become_teacher.html')


@teacher.route('/admin/promote-to-teacher/<int:user_id>', methods=['POST'])
@login_required
def promote_to_teacher(user_id):
    """Admin route to promote a user to teacher"""
    if not current_user.is_admin and current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    user = User.query.get_or_404(user_id)
    user.role = 'teacher'
    db.session.commit()
    
    flash(f'{user.name} has been promoted to teacher.', 'success')
    return redirect(url_for('auth.profile', user_id=user_id))
