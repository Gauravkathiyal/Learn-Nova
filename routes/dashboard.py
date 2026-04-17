"""
Dashboard Routes - User Dashboard
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request     # type: ignore[import]
from flask_login import login_required, current_user  # type: ignore[import]
from models import Enrollment, Result, Timetable, Course  # type: ignore[attr-defined]
from extensions import db  # type: ignore[import]
from sqlalchemy import func
from services.recommendation_service import RecommendationService

dashboard = Blueprint('dashboard', __name__)


@dashboard.route('/dashboard')
@login_required
def index():
    """User dashboard - shows enrolled courses, progress, etc."""
    enrollments = Enrollment.query.filter_by(user_id=current_user.id, status='active').all()
    recent_results = Result.query.filter_by(user_id=current_user.id).order_by(Result.submitted_at.desc()).limit(5).all()
    active_timetable = Timetable.query.filter_by(user_id=current_user.id, is_active=True).first()
    
    # Calculate stats
    total_courses = len(enrollments)
    certificates_earned = Enrollment.query.filter_by(
        user_id=current_user.id, 
        status='completed'
    ).count()
    total_study_time = current_user.total_study_time
    avg_score = 0
    if recent_results:
        avg_score = sum(r.percentage for r in recent_results) / len(recent_results)
    
    # Get courses with progress
    enrolled_courses = []
    total_progress = 0
    for e in enrollments:
        course = Course.query.get(e.course_id)
        if course:
            enrolled_courses.append({
                'enrollment': e,
                'course': course
            })
            total_progress += e.progress_percent
    
    # Calculate average progress
    if enrollments:
        total_progress = total_progress // len(enrollments)
    
    # Get personalized recommendations
    recommended_courses = []
    try:
        recommendations = RecommendationService.get_recommendations(
            user_id=current_user.id,
            method='hybrid',
            n=6
        )
        
        # Get course details
        for rec in recommendations:
            course = Course.query.get(rec['course_id'])
            if course and course.is_published:
                recommended_courses.append({
                    'course': course,
                    'score': rec['score']
                })
    except Exception as e:
        # If recommendations fail, get popular courses
        try:
            popular = RecommendationService.get_popular_courses(6)
            for pop in popular:
                course = Course.query.get(pop['course_id'])
                if course and course.is_published:
                    recommended_courses.append({
                        'course': course,
                        'score': pop.get('popularity_score', 0)
                    })
        except:
            pass
    
    return render_template('dashboard.html',
                          enrollments=enrolled_courses,
                          recent_results=recent_results,
                          timetable=active_timetable,
                          total_courses=total_courses,
                          certificates_earned=certificates_earned,
                          total_study_time=total_study_time,
                          avg_score=round(avg_score, 1),
                          total_progress=total_progress,
                          recommended_courses=recommended_courses)


@dashboard.route('/my-courses')
@login_required
def my_courses():
    """User's enrolled courses"""
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).order_by(Enrollment.enrolled_at.desc()).all()
    return render_template('my_courses.html', enrollments=enrollments)


@dashboard.route('/my-results')
@login_required
def my_results():
    """User's test results"""
    results = Result.query.filter_by(user_id=current_user.id).order_by(Result.submitted_at.desc()).all()
    return render_template('my_results.html', results=results)


@dashboard.route('/progress')
@login_required
def progress():
    """User's learning progress"""
    enrollments = Enrollment.query.filter_by(user_id=current_user.id, status='active').all()
    results = Result.query.filter_by(user_id=current_user.id).all()
    
    # Calculate statistics
    total_progress = sum(e.progress_percent for e in enrollments) / len(enrollments) if enrollments else 0
    
    avg_score = sum(r.percentage for r in results) / len(results) if results else 0
    
    return render_template('progress.html',
                          enrollments=enrollments,
                          results=results,
                          total_progress=total_progress,
                          avg_score=avg_score)
