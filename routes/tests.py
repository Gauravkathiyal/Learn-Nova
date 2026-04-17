"""
Tests Routes - Test/Quiz pages
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify  # type: ignore[import]
from flask_login import login_required, current_user  # type: ignore[import]
from models import Test, Question, Result  # type: ignore[attr-defined]
from extensions import db  # type: ignore[import]

tests = Blueprint('tests', __name__)


# Age-based category structure for Mock Test Series
TEST_CATEGORIES = {
    '6-10': {
        'name': '6–10 Years',
        'icon': '👶',
        'subcategories': [
            {'name': 'Basic Math', 'slug': 'basic-math'},
            {'name': 'Science', 'slug': 'science'},
            {'name': 'English', 'slug': 'english'},
            {'name': 'Logical Thinking', 'slug': 'logical-thinking'},
            {'name': 'Fun Quizzes', 'slug': 'fun-quizzes'}
        ]
    },
    '11-12': {
        'name': '11–12 (School Level)',
        'icon': '🏫',
        'subcategories': [
            {'name': 'Board Exam Preparation', 'slug': 'board-exam'},
            {'name': 'PCM Focus', 'slug': 'pcm'},
            {'name': 'PCB Focus', 'slug': 'pcb'},
            {'name': 'Foundation for Competitive Exams', 'slug': 'foundation'}
        ]
    },
    'graduate': {
        'name': 'Graduate Level',
        'icon': '🎓',
        'subcategories': [
            {'name': 'MCA / BCA / B.Tech', 'slug': 'mca-bca-btech'},
            {'name': 'Programming', 'slug': 'programming'},
            {'name': 'Data Structures', 'slug': 'data-structures'},
            {'name': 'AI / ML', 'slug': 'ai-ml'},
            {'name': 'Web Development', 'slug': 'web-development'}
        ]
    },
    'skill': {
        'name': 'Skill Enhancement',
        'icon': '💼',
        'subcategories': [
            {'name': 'Coding', 'slug': 'coding'},
            {'name': 'Data Analytics', 'slug': 'data-analytics'},
            {'name': 'Cybersecurity', 'slug': 'cybersecurity'},
            {'name': 'AI Tools', 'slug': 'ai-tools'},
            {'name': 'Soft Skills', 'slug': 'soft-skills'}
        ]
    },
    'govt': {
        'name': 'Govt Exam Preparation',
        'icon': '🏛',
        'subcategories': [
            {'name': 'UPSC', 'slug': 'upsc'},
            {'name': 'CDS', 'slug': 'cds'},
            {'name': 'SSC', 'slug': 'ssc'},
            {'name': 'Banking', 'slug': 'banking'},
            {'name': 'State PSC', 'slug': 'state-psc'},
            {'name': 'Defence Exams', 'slug': 'defence'}
        ]
    }
}


@tests.route('/tests')
def all_tests():
    """All available tests with category structure"""
    selected_category = request.args.get('category')
    difficulty = request.args.get('difficulty')
    
    # Get all published tests
    query = Test.query.filter_by(is_published=True)
    
    if selected_category:
        query = query.filter_by(category=selected_category)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    
    tests_list = query.all()
    
    return render_template('test_list.html', 
                           tests=tests_list, 
                           selected_category=selected_category, 
                           selected_difficulty=difficulty,
                           test_categories=TEST_CATEGORIES)


@tests.route('/test/<int:test_id>')
def test_detail(test_id):
    """Test detail page"""
    test = Test.query.get_or_404(test_id)
    question_count = test.questions.count()
    return render_template('test_detail.html', test=test, question_count=question_count)


@tests.route('/test/<int:test_id>/start')
@login_required
def start_test(test_id):
    """Start a test - creates a result entry"""
    test = Test.query.get_or_404(test_id)
    
    # Check if user already has an in-progress result
    existing_result = Result.query.filter_by(
        user_id=current_user.id,
        test_id=test_id,
        status='in_progress'
    ).first()
    
    if existing_result:
        return redirect(url_for('tests.take_test', result_id=existing_result.id))
    
    # Create new result
    result = Result(
        user_id=current_user.id,
        test_id=test_id,
        status='in_progress'
    )
    
    db.session.add(result)
    db.session.commit()
    
    return redirect(url_for('tests.take_test', result_id=result.id))


@tests.route('/test/result/<int:result_id>')
@login_required
def take_test(result_id):
    """Take test page - shows questions"""
    result = Result.query.get_or_404(result_id)
    
    if result.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard.index'))
    
    test = result.test
    questions = test.questions.order_by(Question.order_index).all()
    
    return render_template('test.html', result=result, test=test, questions=questions)


@tests.route('/test/result/<int:result_id>/submit', methods=['POST'])
@login_required
def submit_test(result_id):
    """Submit test - calculate score"""
    result = Result.query.get_or_404(result_id)
    
    if result.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Get answers from form
    answers = request.get_json()
    
    from typing import cast
    
    test = result.test
    questions = test.questions.all()
    
    score_value: float = 0.0
    total_marks: float = 0.0
    correct: int = 0
    wrong: int = 0
    unattempted: int = 0
    
    for q in questions:
        total_marks = cast(float, total_marks) + float(q.marks or 0)
        question_id = str(q.id)
        
        if question_id not in answers or not answers[question_id]:
            unattempted += 1
            continue
        
        user_answer = answers[question_id]
        
        if user_answer == q.correct_answer:
            score_value = cast(float, score_value) + float(q.marks or 0)
            correct += 1
        else:
            score_value = cast(float, score_value) - float(q.negative_marks or 0)
            wrong += 1
    
    # Update result
    result.score = int(max(0.0, score_value))
    result.total_marks = int(total_marks)
    result.correct_answers = correct
    result.wrong_answers = wrong
    result.unattempted = unattempted
    result.status = 'completed'
    result.calculate_percentage()
    
    # Save answers as JSON
    import json
    result.answers = json.dumps(answers)
    
    db.session.commit()
    
    # Update user streak
    current_user.increment_streak()
    
    return jsonify({
        'success': True,
        'score': result.score,
        'total_marks': total_marks,
        'percentage': result.percentage,
        'correct': correct,
        'wrong': wrong,
        'unattempted': unattempted
    })
