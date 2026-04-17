"""
Recommendation Tasks - Background tasks for recommendation system
"""

from celery import Celery
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery = Celery('learnnova')

# Configure Celery
celery.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Asia/Kolkata',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routes
celery.conf.task_routes = {
    'tasks.recommendation_tasks.train_collaborative_filtering_model': {'queue': 'recommendations'},
    'tasks.recommendation_tasks.update_recommendations_cache': {'queue': 'recommendations'},
    'tasks.recommendation_tasks.log_recommendation_analytics': {'queue': 'analytics'},
}

# Schedule for periodic tasks
celery.conf.beat_schedule = {
    'train-model-daily': {
        'task': 'tasks.recommendation_tasks.train_collaborative_filtering_model',
        'schedule': timedelta(days=1),  # Run daily
    },
    'update-cache-hourly': {
        'task': 'tasks.recommendation_tasks.update_recommendations_cache',
        'schedule': timedelta(hours=1),  # Run hourly
    },
    'log-analytics-daily': {
        'task': 'tasks.recommendation_tasks.log_recommendation_analytics',
        'schedule': timedelta(days=1),  # Run daily
    },
}


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def train_collaborative_filtering_model(self):
    """
    Train the collaborative filtering model
    
    This task trains the ML model with all available enrollment data.
    Should be run daily or when significant new data is available.
    """
    try:
        logger.info("Starting collaborative filtering model training...")
        
        # Import here to avoid circular imports
        from services.recommendation_service import RecommendationService
        
        # Train the model
        success = RecommendationService.train_model()
        
        if success:
            logger.info("Collaborative filtering model trained successfully")
            return {
                'status': 'success',
                'message': 'Model trained successfully'
            }
        else:
            logger.error("Failed to train collaborative filtering model")
            return {
                'status': 'failed',
                'message': 'Model training failed'
            }
            
    except Exception as e:
        logger.error(f"Error in train_collaborative_filtering_model: {str(e)}")
        
        # Retry the task
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for model training task")
            return {
                'status': 'failed',
                'message': f'Max retries exceeded: {str(e)}'
            }


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def update_recommendations_cache(self):
    """
    Update recommendations cache for active users
    
    This task pre-computes and caches recommendations for users
    who have been active in the last 7 days.
    """
    try:
        logger.info("Starting recommendations cache update...")
        
        # Import here to avoid circular imports
        from services.recommendation_service import RecommendationService
        from models.user import User
        from models.course import Enrollment
        from datetime import datetime, timedelta
        
        # Get users active in last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        active_users = User.query.join(Enrollment).filter(
            Enrollment.updated_at >= seven_days_ago,
            Enrollment.status.in_(['active', 'completed'])
        ).distinct().all()
        
        updated_count = 0
        for user in active_users:
            try:
                # Get and cache recommendations for each method
                for method in ['hybrid', 'collaborative', 'keyword']:
                    RecommendationService.get_recommendations(
                        user_id=user.id,
                        method=method,
                        n=6,
                        use_cache=False  # Force refresh
                    )
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating cache for user {user.id}: {str(e)}")
                continue
        
        logger.info(f"Updated recommendations cache for {updated_count} users")
        return {
            'status': 'success',
            'message': f'Updated cache for {updated_count} users',
            'users_updated': updated_count
        }
        
    except Exception as e:
        logger.error(f"Error in update_recommendations_cache: {str(e)}")
        
        # Retry the task
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for cache update task")
            return {
                'status': 'failed',
                'message': f'Max retries exceeded: {str(e)}'
            }


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def log_recommendation_analytics(self):
    """
    Log recommendation system analytics
    
    This task logs various metrics about the recommendation system
    for monitoring and optimization purposes.
    """
    try:
        logger.info("Starting recommendation analytics logging...")
        
        # Import here to avoid circular imports
        from services.recommendation_service import RecommendationService
        from models.course import Course, Enrollment
        from models.user import User
        from extensions import db
        from sqlalchemy import func
        
        # Get statistics
        stats = RecommendationService.get_recommendation_stats()
        
        # Get additional metrics
        total_courses = Course.query.filter_by(is_published=True).count()
        total_enrollments = Enrollment.query.filter(
            Enrollment.status.in_(['active', 'completed'])
        ).count()
        
        # Get enrollment distribution by category
        category_stats = db.session.query(
            Course.category,
            func.count(Enrollment.id).label('enrollment_count')
        ).join(Enrollment).filter(
            Enrollment.status.in_(['active', 'completed'])
        ).group_by(Course.category).all()
        
        # Log analytics
        analytics_data = {
            'timestamp': str(datetime.utcnow()),
            'total_users': stats.get('total_users', 0),
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
            'model_trained': stats.get('model_trained', False),
            'cache_stats': stats.get('cache_stats', {}),
            'category_distribution': [
                {'category': cat, 'enrollments': count}
                for cat, count in category_stats
            ]
        }
        
        logger.info(f"Recommendation analytics: {analytics_data}")
        
        return {
            'status': 'success',
            'message': 'Analytics logged successfully',
            'analytics': analytics_data
        }
        
    except Exception as e:
        logger.error(f"Error in log_recommendation_analytics: {str(e)}")
        
        # Retry the task
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for analytics logging task")
            return {
                'status': 'failed',
                'message': f'Max retries exceeded: {str(e)}'
            }


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def invalidate_user_recommendations_cache(self, user_id):
    """
    Invalidate recommendations cache for a specific user
    
    Args:
        user_id: User ID to invalidate cache for
    """
    try:
        logger.info(f"Invalidating recommendations cache for user {user_id}...")
        
        # Import here to avoid circular imports
        from services.recommendation_service import RecommendationService
        
        # Invalidate cache
        RecommendationService.invalidate_user_cache(user_id)
        
        logger.info(f"Cache invalidated for user {user_id}")
        return {
            'status': 'success',
            'message': f'Cache invalidated for user {user_id}'
        }
        
    except Exception as e:
        logger.error(f"Error invalidating cache for user {user_id}: {str(e)}")
        
        # Retry the task
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for cache invalidation task for user {user_id}")
            return {
                'status': 'failed',
                'message': f'Max retries exceeded: {str(e)}'
            }


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def batch_train_and_update(self):
    """
    Batch task to train model and update cache
    
    This task combines model training and cache update
    for efficiency.
    """
    try:
        logger.info("Starting batch training and cache update...")
        
        # Train model
        train_result = train_collaborative_filtering_model.apply()
        
        if train_result.get('status') == 'success':
            # Update cache
            cache_result = update_recommendations_cache.apply()
            
            logger.info("Batch training and cache update completed")
            return {
                'status': 'success',
                'message': 'Batch training and cache update completed',
                'train_result': train_result,
                'cache_result': cache_result
            }
        else:
            logger.error("Model training failed, skipping cache update")
            return {
                'status': 'failed',
                'message': 'Model training failed',
                'train_result': train_result
            }
            
    except Exception as e:
        logger.error(f"Error in batch_train_and_update: {str(e)}")
        
        # Retry the task
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for batch training task")
            return {
                'status': 'failed',
                'message': f'Max retries exceeded: {str(e)}'
            }
