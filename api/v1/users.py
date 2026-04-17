"""
API v1 User Routes
"""

from flask import request, jsonify  # type: ignore[import]
from flask_jwt_extended import jwt_required, get_jwt_identity  # type: ignore[import]
from models.user import User  # type: ignore[attr-defined]
from extensions import db  # type: ignore[attr-defined]
from api.v1 import v1  # type: ignore[attr-defined]

# Use db.session.get() instead of deprecated Query.get() for SQLAlchemy 2.0+

@v1.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users (admin only)"""
    users = db.session.query(User).all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200


@v1.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get a specific user"""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200


@v1.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update user profile"""
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if data is None:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'name' in data:
        user.name = data['name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'category' in data:
        user.category = data['category']
    if 'target_exam' in data:
        user.target_exam = data['target_exam']
    if 'study_hours_per_day' in data:
        user.study_hours_per_day = data['study_hours_per_day']
    
    db.session.commit()
    
    return jsonify({'message': 'User updated successfully', 'user': user.to_dict()}), 200


@v1.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete a user (admin only)"""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200


@v1.route('/users/<int:user_id>/progress', methods=['GET'])
@jwt_required()
def get_user_progress(user_id):
    """Get user's learning progress"""
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    enrollments = user.enrollments
    progress_data = []
    
    for enrollment in enrollments:
        progress_data.append({
            'course_id': enrollment.course_id,
            'course_title': enrollment.course.title,
            'progress_percent': enrollment.progress_percent,
            'chapters_completed': enrollment.chapters_completed,
            'total_chapters': len(enrollment.course.chapters),
            'enrolled_at': enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
            'status': enrollment.status
        })
    
    return jsonify({'progress': progress_data}), 200
