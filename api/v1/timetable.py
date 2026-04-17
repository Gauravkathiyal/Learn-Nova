"""
API v1 Timetable Routes
"""

from flask import request, jsonify  # type: ignore[import]
from flask_jwt_extended import jwt_required, get_jwt_identity  # type: ignore[import]
from models.timetable import Timetable, TimetableItem  # type: ignore[import]
from extensions import db  # type: ignore[import]
from api.v1 import v1  # type: ignore[import]

@v1.route('/timetable', methods=['GET'])
@jwt_required()
def get_timetable():
    """Get current user's timetable"""
    user_id = get_jwt_identity()
    
    timetable = Timetable.query.filter_by(user_id=user_id).first()
    if not timetable:
        return jsonify({'timetable': None, 'items': []}), 200
    
    items = TimetableItem.query.filter_by(timetable_id=timetable.id).order_by(
        TimetableItem.day_of_week, TimetableItem.start_time
    ).all()
    
    return jsonify({
        'timetable': timetable.to_dict(),
        'items': [item.to_dict() for item in items]
    }), 200


@v1.route('/timetable', methods=['POST'])
@jwt_required()
def create_timetable():
    """Create or update user's timetable"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    timetable = Timetable.query.filter_by(user_id=user_id).first()
    
    if not timetable:
        timetable = Timetable(user_id=user_id)
        db.session.add(timetable)
        db.session.flush()
    
    # Clear existing items
    TimetableItem.query.filter_by(timetable_id=timetable.id).delete()
    
    # Add new items
    items_data = data.get('items', [])
    for item_data in items_data:
        item = TimetableItem(
            timetable_id=timetable.id,
            day_of_week=item_data.get('day_of_week'),
            start_time=item_data.get('start_time'),
            end_time=item_data.get('end_time'),
            subject=item_data.get('subject'),
            topic=item_data.get('topic'),
            notes=item_data.get('notes')
        )
        db.session.add(item)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Timetable updated successfully',
        'timetable': timetable.to_dict()
    }), 200


@v1.route('/timetable/generate', methods=['POST'])
@jwt_required()
def generate_ai_timetable():
    """Generate AI-powered study timetable"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Get user preferences
    available_hours = data.get('available_hours', [])
    subjects = data.get('subjects', [])
    goals = data.get('goals', [])
    preferred_study_time = data.get('preferred_study_time', 'morning')
    
    # This is a placeholder - in production, integrate with AI service
    # For now, generate a basic timetable based on preferences
    
    timetable = Timetable.query.filter_by(user_id=user_id).first()
    if not timetable:
        timetable = Timetable(user_id=user_id)
        db.session.add(timetable)
        db.session.flush()
    
    # Clear existing items
    TimetableItem.query.filter_by(timetable_id=timetable.id).delete()
    
    # Generate basic schedule (placeholder AI logic)
    day_schedule = {
        0: ['09:00-11:00 Math', '14:00-16:00 Physics'],
        1: ['09:00-11:00 Chemistry', '14:00-16:00 Biology'],
        2: ['09:00-11:00 English', '14:00-16:00 History'],
        3: ['09:00-11:00 Math', '14:00-16:00 Physics'],
        4: ['09:00-11:00 Chemistry', '14:00-16:00 Biology'],
        5: ['09:00-11:00 Review', '14:00-16:00 Practice'],
        6: ['10:00-12:00 Self Study', '14:00-16:00 Project Work']
    }
    
    for day, schedule in day_schedule.items():
        for session in schedule:
            parts = session.split(' ')
            time_parts = parts[0].split('-')
            subject = ' '.join(parts[1:])  # type: ignore[assignment]
            
            item = TimetableItem(
                timetable_id=timetable.id,
                day_of_week=day,
                start_time=time_parts[0],
                end_time=time_parts[1],
                subject=subject,
                topic='',
                notes='AI Generated'
            )
            db.session.add(item)
    
    db.session.commit()
    
    items = TimetableItem.query.filter_by(timetable_id=timetable.id).order_by(
        TimetableItem.day_of_week, TimetableItem.start_time
    ).all()
    
    return jsonify({
        'message': 'AI timetable generated successfully',
        'timetable': timetable.to_dict(),
        'items': [item.to_dict() for item in items]
    }), 200


@v1.route('/timetable/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_timetable_item(item_id):
    """Update a specific timetable item"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    item = db.session.get(TimetableItem, item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Verify ownership
    timetable = db.session.get(Timetable, item.timetable_id)
    if not timetable or timetable.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if 'subject' in data:
        item.subject = data['subject']
    if 'topic' in data:
        item.topic = data['topic']
    if 'start_time' in data:
        item.start_time = data['start_time']
    if 'end_time' in data:
        item.end_time = data['end_time']
    if 'notes' in data:
        item.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Item updated successfully',
        'item': item.to_dict()
    }), 200


@v1.route('/timetable/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_timetable_item(item_id):
    """Delete a timetable item"""
    user_id = get_jwt_identity()
    
    item = db.session.get(TimetableItem, item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Verify ownership
    timetable = db.session.get(Timetable, item.timetable_id)
    if not timetable or timetable.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': 'Item deleted successfully'}), 200
