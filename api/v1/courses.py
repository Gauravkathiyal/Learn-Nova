"""
API v1 Course Routes
"""

from flask import request, jsonify  # type: ignore[import]
from flask_jwt_extended import jwt_required, get_jwt_identity  # type: ignore[import]
from models.course import Course, Chapter, Enrollment  # type: ignore[import]
from models.user import User  # type: ignore[import]
from extensions import db  # type: ignore[import]
from api.v1 import v1  # type: ignore[import]

@v1.route('/courses', methods=['GET'])
def get_courses():
    """Get all courses"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category = request.args.get('category')
    search = request.args.get('search')
    
    query = Course.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(Course.title.ilike(f'%{search}%'))
    
    courses = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'courses': [c.to_dict() for c in courses.items],
        'total': courses.total,
        'page': courses.page,
        'pages': courses.pages
    }), 200


@v1.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """Get a specific course with chapters"""
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    return jsonify({'course': course.to_dict()}), 200


@v1.route('/courses/<int:course_id>/enroll', methods=['POST'])
@jwt_required()
def enroll_course(course_id):
    """Enroll in a course"""
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    existing_enrollment = Enrollment.query.filter_by(
        user_id=user_id, course_id=course_id
    ).first()
    
    if existing_enrollment:
        return jsonify({'error': 'Already enrolled in this course'}), 400
    
    enrollment = Enrollment(user_id=user_id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()
    
    return jsonify({
        'message': 'Successfully enrolled in course',
        'enrollment': enrollment.to_dict()
    }), 201


@v1.route('/courses/<int:course_id>/chapters/<int:chapter_id>/complete', methods=['POST'])
@jwt_required()
def complete_chapter(course_id, chapter_id):
    """Mark a chapter as completed"""
    user_id = get_jwt_identity()
    
    enrollment = Enrollment.query.filter_by(
        user_id=user_id, course_id=course_id
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course'}), 400
    
    # Get chapter - course relationship is loaded via backref
    chapter = db.session.get(Chapter, chapter_id)
    if not chapter or chapter.course_id != course_id:
        return jsonify({'error': 'Chapter not found'}), 404
    
    # Get total chapters count
    total_chapters = chapter.course.chapters.count()
    
    # Check for potential duplicate completion (basic validation)
    # Note: A proper implementation would track completed chapters in a separate table
    max_possible_completed = min(enrollment.chapters_completed + 1, total_chapters)
    
    # Update progress - increment chapters_completed (capped at total)
    enrollment.chapters_completed = max_possible_completed
    enrollment.progress_percent = int((enrollment.chapters_completed / total_chapters) * 100) if total_chapters > 0 else 0
    
    db.session.commit()
    
    return jsonify({
        'message': 'Chapter marked as completed',
        'progress': enrollment.progress_percent
    }), 200


@v1.route('/my-courses', methods=['GET'])
@jwt_required()
def get_my_courses():
    """Get enrolled courses for current user"""
    user_id = get_jwt_identity()
    
    enrollments = Enrollment.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'courses': [e.to_dict() for e in enrollments]
    }), 200
