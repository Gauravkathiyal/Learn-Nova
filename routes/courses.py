"""
Courses Routes - Course pages
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request  # type: ignore[import]
from flask_login import login_required, current_user  # type: ignore[import]
from models import Course, Chapter, Enrollment, Category  # type: ignore[attr-defined]
from extensions import db  # type: ignore[import]

courses = Blueprint('courses', __name__)


@courses.route('/courses')
def index():
    """Courses listing page with categories"""
    # Get categories with course counts
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
    
    # Get all courses from backend
    courses_list = Course.query.order_by(Course.created_at.desc()).all()
    
    # Get user's enrolled course IDs if logged in
    enrolled_course_ids = []
    if current_user.is_authenticated:
        enrollments = Enrollment.query.filter_by(user_id=current_user.id, status='active').all()
        enrolled_course_ids = [e.course_id for e in enrollments]
    
    return render_template('courses.html',
                          categories=categories,
                          courses=courses_list,
                          enrolled_course_ids=enrolled_course_ids)


@courses.route('/course/<int:course_id>')
def course_detail(course_id):
    """Course detail page"""
    course = Course.query.get_or_404(course_id)
    chapters = Chapter.query.filter_by(course_id=course_id).order_by(Chapter.order_index).all()
    
    # Check if user is enrolled
    is_enrolled = False
    if current_user.is_authenticated:
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
        is_enrolled = bool(enrollment)
    
    # Get similar courses
    similar_courses = []
    try:
        from services.recommendation_service import RecommendationService
        similar = RecommendationService.get_similar_courses(course_id, n=5)
        for sim in similar:
            similar_course = Course.query.get(sim['course_id'])
            if similar_course and similar_course.is_published:
                similar_courses.append({
                    'course': similar_course,
                    'similarity_score': sim['similarity_score']
                })
    except Exception as e:
        # If similar courses fail, get popular courses from same category
        try:
            popular = Course.query.filter_by(
                category=course.category,
                is_published=True
            ).filter(Course.id != course_id).order_by(
                Course.rating.desc(),
                Course.total_students.desc()
            ).limit(5).all()
            
            for pop in popular:
                similar_courses.append({
                    'course': pop,
                    'similarity_score': 0.5
                })
        except:
            pass
    
    return render_template('course_detail.html',
                          course=course,
                          chapters=chapters,
                          is_enrolled=is_enrolled,
                          similar_courses=similar_courses)


@courses.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    """Enroll in a course"""
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing:
        flash('You are already enrolled in this course', 'info')
        return redirect(url_for('courses.course_detail', course_id=course_id))
    
    # Create enrollment
    enrollment = Enrollment(
        user_id=current_user.id,
        course_id=course_id,
        status='active'
    )
    
    db.session.add(enrollment)
    
    # Update course student count
    course.total_students += 1
    
    db.session.commit()
    
    # Invalidate recommendation cache for user
    try:
        from services.recommendation_service import RecommendationService
        RecommendationService.invalidate_user_cache(current_user.id)
    except:
        pass
    
    flash(f'Successfully enrolled in {course.title}!', 'success')
    return redirect(url_for('courses.course_detail', course_id=course_id))


@courses.route('/enroll/<int:course_id>')
def enrollment_checkout(course_id):
    """Show enrollment checkout page"""
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    is_enrolled = False
    if current_user.is_authenticated:
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
        is_enrolled = bool(enrollment)
    
    # Calculate discount (demo: 50% off)
    original_price = course.price
    discount = 0
    if course.price > 0:
        discount = course.price * 0.5
    final_price = course.price - discount
    
    return render_template('enroll.html',
                          course=course,
                          original_price=original_price,
                          discount=discount,
                          final_price=final_price,
                          is_enrolled=is_enrolled)


@courses.route('/enroll')
def enroll_page():
    """Redirect to courses page"""
    return redirect(url_for('courses.index'))


@courses.route('/course/<int:course_id>/chapter/<int:chapter_id>')
@login_required
def course_chapter(course_id, chapter_id):
    """Course chapter/video page"""
    course = Course.query.get_or_404(course_id)
    chapter = Chapter.query.get_or_404(chapter_id)
    
    # Check if user is enrolled
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id,
        status='active'
    ).first()
    
    if not enrollment and not chapter.is_free_preview:
        flash('Please enroll to access this chapter', 'warning')
        return redirect(url_for('courses.course_detail', course_id=course_id))
    
    return render_template('course_chapter.html',
                          course=course,
                          chapter=chapter)
