"""
Recommendations API - RESTful endpoints for recommendation system
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from functools import wraps
import logging

from services.recommendation_service import RecommendationService
from models.course import Course

logger = logging.getLogger(__name__)

recommendations_api = Blueprint('recommendations_api', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@recommendations_api.route('/api/v1/recommendations', methods=['GET'])
@login_required
def get_recommendations():
    """
    Get personalized course recommendations for current user
    
    Query Parameters:
        method: Recommendation method ('hybrid', 'collaborative', 'keyword')
        n: Number of recommendations (default: 6)
    
    Returns:
        JSON with recommended courses and scores
    """
    try:
        method = request.args.get('method', 'hybrid')
        n = int(request.args.get('n', 6))
        
        # Validate method
        if method not in ['hybrid', 'collaborative', 'keyword']:
            return jsonify({
                'success': False,
                'error': 'Invalid method. Must be one of: hybrid, collaborative, keyword'
            }), 400
        
        # Get recommendations
        recommendations = RecommendationService.get_recommendations(
            user_id=current_user.id,
            method=method,
            n=n
        )
        
        # Get course details
        recommended_courses = []
        for rec in recommendations:
            course = Course.query.get(rec['course_id'])
            if course and course.is_published:
                recommended_courses.append({
                    'course': course.to_dict(),
                    'score': rec['score'],
                    'method': method
                })
        
        return jsonify({
            'success': True,
            'recommendations': recommended_courses,
            'method': method,
            'count': len(recommended_courses)
        })
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get recommendations'
        }), 500


@recommendations_api.route('/api/v1/recommendations/similar/<int:course_id>', methods=['GET'])
@login_required
def get_similar_courses(course_id):
    """
    Get courses similar to a given course
    
    Path Parameters:
        course_id: ID of the course to find similar courses for
    
    Query Parameters:
        n: Number of similar courses to return (default: 5)
    
    Returns:
        JSON with similar courses and similarity scores
    """
    try:
        n = int(request.args.get('n', 5))
        
        # Get similar courses
        similar = RecommendationService.get_similar_courses(course_id, n)
        
        # Get course details
        similar_courses = []
        for sim in similar:
            course = Course.query.get(sim['course_id'])
            if course and course.is_published:
                similar_courses.append({
                    'course': course.to_dict(),
                    'similarity_score': sim['similarity_score']
                })
        
        return jsonify({
            'success': True,
            'similar_courses': similar_courses,
            'course_id': course_id,
            'count': len(similar_courses)
        })
        
    except Exception as e:
        logger.error(f"Error getting similar courses: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get similar courses'
        }), 500


@recommendations_api.route('/api/v1/recommendations/popular', methods=['GET'])
@login_required
def get_popular_courses():
    """
    Get globally popular courses
    
    Query Parameters:
        n: Number of popular courses to return (default: 6)
    
    Returns:
        JSON with popular courses and popularity scores
    """
    try:
        n = int(request.args.get('n', 6))
        
        # Get popular courses
        popular = RecommendationService.get_popular_courses(n)
        
        # Get course details
        popular_courses = []
        for pop in popular:
            course = Course.query.get(pop['course_id'])
            if course and course.is_published:
                popular_courses.append({
                    'course': course.to_dict(),
                    'enrollment_count': pop.get('enrollment_count', 0),
                    'avg_progress': pop.get('avg_progress', 0),
                    'popularity_score': pop.get('popularity_score', 0)
                })
        
        return jsonify({
            'success': True,
            'popular_courses': popular_courses,
            'count': len(popular_courses)
        })
        
    except Exception as e:
        logger.error(f"Error getting popular courses: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get popular courses'
        }), 500


@recommendations_api.route('/api/v1/recommendations/train', methods=['POST'])
@login_required
@admin_required
def trigger_training():
    """
    Trigger model training (admin only)
    
    Returns:
        JSON with training status
    """
    try:
        success = RecommendationService.train_model()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Model training completed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Model training failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to train model'
        }), 500


@recommendations_api.route('/api/v1/recommendations/stats', methods=['GET'])
@login_required
@admin_required
def get_stats():
    """
    Get recommendation system statistics (admin only)
    
    Returns:
        JSON with system statistics
    """
    try:
        stats = RecommendationService.get_recommendation_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get statistics'
        }), 500


@recommendations_api.route('/api/v1/recommendations/cache/invalidate', methods=['POST'])
@login_required
@admin_required
def invalidate_cache():
    """
    Invalidate recommendation cache (admin only)
    
    Request Body (optional):
        user_id: Invalidate cache for specific user
        course_id: Invalidate cache for specific course
    
    Returns:
        JSON with invalidation status
    """
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        course_id = data.get('course_id')
        
        if user_id:
            RecommendationService.invalidate_user_cache(user_id)
            message = f'Cache invalidated for user {user_id}'
        elif course_id:
            from services.cache_service import cache_service
            cache_service.invalidate_course_cache(course_id)
            message = f'Cache invalidated for course {course_id}'
        else:
            from services.cache_service import cache_service
            cache_service.delete_pattern("user:*:recommendations:*")
            cache_service.delete_pattern("course:*:similar:*")
            message = 'All recommendation caches invalidated'
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to invalidate cache'
        }), 500
