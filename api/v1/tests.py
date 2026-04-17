"""
API v1 Test/Quiz Routes
"""

from datetime import datetime, timezone

from flask import jsonify, request  # type: ignore[import]
from flask_jwt_extended import get_jwt_identity, jwt_required  # type: ignore[import]
from extensions import db  # type: ignore[import]
from models import Test, Question, Result  # type: ignore[import]
from api.v1 import v1  # type: ignore[import]

@v1.route('/tests', methods=['GET'])
@jwt_required()
def get_tests():
    """Get all available tests"""
    tests = Test.query.filter_by(is_published=True).all()
    return jsonify({'tests': [t.to_dict() for t in tests]}), 200


@v1.route('/tests/<int:test_id>', methods=['GET'])
@jwt_required()
def get_test(test_id):
    """Get a specific test with questions"""
    test = db.session.get(Test, test_id)
    if not test:
        return jsonify({'error': 'Test not found'}), 404
    
    # Eager load questions to avoid N+1 query
    questions = Question.query.filter_by(test_id=test_id).all()
    test_dict = test.to_dict()
    test_dict['questions'] = [q.to_dict() for q in questions]
    
    return jsonify({'test': test_dict}), 200


@v1.route('/tests/<int:test_id>/start', methods=['POST'])
@jwt_required()
def start_test(test_id):
    """Start a test"""
    user_id = get_jwt_identity()
    
    test = db.session.get(Test, test_id)
    if not test:
        return jsonify({'error': 'Test not found'}), 404
    
    # Create a new result entry
    result = Result(
        user_id=user_id,
        test_id=test_id,
        score=0,
        status='in_progress'
    )
    db.session.add(result)
    db.session.commit()
    
    # Eager load questions for the test response
    questions = Question.query.filter_by(test_id=test_id).all()
    test_dict = test.to_dict()
    test_dict['questions'] = [q.to_dict() for q in questions]
    
    return jsonify({
        'message': 'Test started',
        'result_id': result.id,
        'test': test_dict
    }), 201


@v1.route('/tests/<int:test_id>/submit', methods=['POST'])
@jwt_required()
def submit_test(test_id):
    """Submit test answers"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    test = db.session.get(Test, test_id)
    if not test:
        return jsonify({'error': 'Test not found'}), 404
    
    # Get or create result
    result = Result.query.filter_by(
        user_id=user_id, test_id=test_id, status='in_progress'
    ).first()
    
    if not result:
        return jsonify({'error': 'No active test session found'}), 400
    
    # Eager load questions to avoid N+1 query
    questions = Question.query.filter_by(test_id=test_id).all()
    
    answers = data.get('answers', {})
    score = 0
    total_questions = len(questions)
    
    for question in questions:
        user_answer = answers.get(str(question.id))
        # Convert user_answer to string to handle both int and str inputs
        user_answer_str = str(user_answer) if user_answer is not None else None
        # Handle null correct_answer to avoid AttributeError
        if user_answer_str and question.correct_answer:
            if user_answer_str.lower() == question.correct_answer.lower():
                score += 1
    
    # Calculate percentage
    percentage = int((score / total_questions) * 100) if total_questions > 0 else 0
    
    result.percentage = percentage
    result.score = score
    result.total_marks = test.total_marks
    result.status = 'completed'
    result.submitted_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify({
        'message': 'Test submitted successfully',
        'result': result.to_dict(),
        'score': score,
        'total_questions': total_questions,
        'percentage': percentage
    }), 200


@v1.route('/my-results', methods=['GET'])
@jwt_required()
def get_my_results():
    """Get current user's test results"""
    user_id = get_jwt_identity()
    
    results = Result.query.filter_by(user_id=user_id).order_by(Result.submitted_at.desc()).all()
    
    return jsonify({'results': [r.to_dict() for r in results]}), 200
