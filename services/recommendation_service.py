"""
Recommendation Service - Unified recommendation engine
"""

import logging
from routes.ml_recommendation import (
    train_recommender,
    get_ml_recommendations,
    get_popular_courses,
    get_similar_courses,
    recommender
)
from services.cache_service import cache_service
from models.course import Course, Enrollment
from models.user import User
from extensions import db

logger = logging.getLogger(__name__)

class RecommendationService:
    """Unified recommendation service combining all methods"""
    
    @staticmethod
    def get_recommendations(user_id, method='hybrid', n=6, use_cache=True):
        """
        Get personalized recommendations for a user
        
        Args:
            user_id: User ID
            method: 'hybrid', 'collaborative', 'keyword'
            n: Number of recommendations
            use_cache: Whether to use cached recommendations
            
        Returns:
            List of recommended courses with scores
        """
        try:
            # Check cache first
            if use_cache:
                cached = cache_service.get_cached_recommendations(user_id, method, n)
                if cached:
                    logger.info(f"Cache hit for user {user_id} recommendations")
                    return cached
            
            # Get recommendations based on method
            if method == 'collaborative':
                recommendations = RecommendationService._get_collaborative_recommendations(user_id, n)
            elif method == 'keyword':
                recommendations = RecommendationService._get_keyword_recommendations(user_id, n)
            else:  # hybrid
                recommendations = RecommendationService._get_hybrid_recommendations(user_id, n)
            
            # Cache recommendations
            if recommendations and use_cache:
                cache_service.cache_recommendations(user_id, method, n, recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def _get_collaborative_recommendations(user_id, n):
        """Get collaborative filtering recommendations"""
        return get_ml_recommendations(user_id, n, method='hybrid')
    
    @staticmethod
    def _get_keyword_recommendations(user_id, n):
        """Get keyword-based recommendations based on user preferences"""
        try:
            user = User.query.get(user_id)
            if not user:
                return []
            
            # Get user preferences
            user_category = user.category
            user_target_exam = user.target_exam
            
            # Build query based on preferences
            query = Course.query.filter_by(is_published=True)
            
            # Filter by category if available
            if user_category:
                query = query.filter_by(category=user_category)
            
            # Get courses user is already enrolled in
            enrolled_course_ids = [
                e.course_id for e in Enrollment.query.filter_by(
                    user_id=user_id, 
                    status='active'
                ).all()
            ]
            
            # Exclude enrolled courses
            if enrolled_course_ids:
                query = query.filter(Course.id.notin_(enrolled_course_ids))
            
            # Order by rating and popularity
            courses = query.order_by(
                Course.rating.desc(),
                Course.total_students.desc()
            ).limit(n).all()
            
            # Format recommendations
            recommendations = [
                {
                    'course_id': course.id,
                    'score': (course.rating / 5.0) * 0.7 + (min(course.total_students, 1000) / 1000.0) * 0.3
                }
                for course in courses
            ]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting keyword recommendations: {str(e)}")
            return []
    
    @staticmethod
    def _get_hybrid_recommendations(user_id, n, cf_weight=0.7, kw_weight=0.3):
        """
        Get hybrid recommendations combining collaborative and keyword-based
        
        Args:
            user_id: User ID
            n: Number of recommendations
            cf_weight: Weight for collaborative filtering (0-1)
            kw_weight: Weight for keyword-based (0-1)
        """
        try:
            # Get collaborative filtering recommendations
            cf_recs = RecommendationService._get_collaborative_recommendations(user_id, n * 2)
            
            # Get keyword-based recommendations
            kw_recs = RecommendationService._get_keyword_recommendations(user_id, n * 2)
            
            # Combine scores
            combined_scores = {}
            
            for rec in cf_recs:
                course_id = rec['course_id']
                combined_scores[course_id] = rec['score'] * cf_weight
            
            for rec in kw_recs:
                course_id = rec['course_id']
                if course_id in combined_scores:
                    combined_scores[course_id] += rec['score'] * kw_weight
                else:
                    combined_scores[course_id] = rec['score'] * kw_weight
            
            # Sort by combined score
            sorted_courses = sorted(
                combined_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Return top N
            return [
                {'course_id': course_id, 'score': float(score)}
                for course_id, score in sorted_courses[:n]
            ]
            
        except Exception as e:
            logger.error(f"Error getting hybrid recommendations: {str(e)}")
            return []
    
    @staticmethod
    def get_similar_courses(course_id, n=5, use_cache=True):
        """Get courses similar to given course"""
        try:
            # Check cache
            if use_cache:
                cached = cache_service.get_cached_similar_courses(course_id, n)
                if cached:
                    return cached
            
            # Get similar courses
            similar = get_similar_courses(course_id, n)
            
            # Cache results
            if similar and use_cache:
                cache_service.cache_similar_courses(course_id, n, similar)
            
            return similar
            
        except Exception as e:
            logger.error(f"Error getting similar courses for {course_id}: {str(e)}")
            return []
    
    @staticmethod
    def get_popular_courses(n=6, use_cache=True):
        """Get globally popular courses"""
        try:
            # Check cache
            if use_cache:
                cached = cache_service.get_cached_popular_courses(n)
                if cached:
                    return cached
            
            # Get popular courses
            popular = get_popular_courses(n)
            
            # Cache results
            if popular and use_cache:
                cache_service.cache_popular_courses(n, popular)
            
            return popular
            
        except Exception as e:
            logger.error(f"Error getting popular courses: {str(e)}")
            return []
    
    @staticmethod
    def train_model():
        """Train the collaborative filtering model"""
        try:
            # Get all enrollments
            enrollments = Enrollment.query.filter(
                Enrollment.status.in_(['active', 'completed'])
            ).all()
            
            # Prepare data
            enrollments_data = [
                {
                    'user_id': e.user_id,
                    'course_id': e.course_id,
                    'progress_percent': e.progress_percent or 0
                }
                for e in enrollments
            ]
            
            # Train model
            success = train_recommender(enrollments_data)
            
            if success:
                logger.info(f"Model trained with {len(enrollments_data)} enrollments")
                # Invalidate all recommendation caches
                cache_service.delete_pattern("user:*:recommendations:*")
                cache_service.delete_pattern("course:*:similar:*")
            
            return success
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate cache for a specific user"""
        cache_service.invalidate_user_cache(user_id)
    
    @staticmethod
    def get_recommendation_stats():
        """Get recommendation system statistics"""
        try:
            total_users = User.query.count()
            total_courses = Course.query.filter_by(is_published=True).count()
            total_enrollments = Enrollment.query.filter(
                Enrollment.status.in_(['active', 'completed'])
            ).count()
            
            cache_stats = cache_service.get_cache_stats()
            
            return {
                'total_users': total_users,
                'total_courses': total_courses,
                'total_enrollments': total_enrollments,
                'model_trained': recommender.is_fitted,
                'cache_stats': cache_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}
