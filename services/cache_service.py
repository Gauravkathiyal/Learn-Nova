"""
Cache Service - Redis-based caching for recommendations
"""

import redis
import json
import pickle
from functools import wraps
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service for recommendations"""
    
    def __init__(self, app=None):
        self.redis_client = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize cache with Flask app"""
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except redis.ConnectionError:
            logger.warning("Redis not available, using in-memory cache")
            self.redis_client = None
    
    def get(self, key):
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set(self, key, value, ttl=3600):
        """Set value in cache with TTL (seconds)"""
        if not self.redis_client:
            return False
        
        try:
            serialized = pickle.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    def delete(self, key):
        """Delete value from cache"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    def delete_pattern(self, pattern):
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache delete pattern error: {str(e)}")
            return False
    
    # Recommendation-specific cache methods
    def get_cached_recommendations(self, user_id, method, n):
        """Get cached recommendations for user"""
        key = f"user:{user_id}:recommendations:{method}:{n}"
        return self.get(key)
    
    def cache_recommendations(self, user_id, method, n, recommendations, ttl=3600):
        """Cache recommendations for user"""
        key = f"user:{user_id}:recommendations:{method}:{n}"
        return self.set(key, recommendations, ttl)
    
    def get_cached_similar_courses(self, course_id, n):
        """Get cached similar courses"""
        key = f"course:{course_id}:similar:{n}"
        return self.get(key)
    
    def cache_similar_courses(self, course_id, n, courses, ttl=86400):
        """Cache similar courses"""
        key = f"course:{course_id}:similar:{n}"
        return self.set(key, courses, ttl)
    
    def get_cached_popular_courses(self, n):
        """Get cached popular courses"""
        key = f"courses:popular:{n}"
        return self.get(key)
    
    def cache_popular_courses(self, n, courses, ttl=21600):
        """Cache popular courses (6 hours)"""
        key = f"courses:popular:{n}"
        return self.set(key, courses, ttl)
    
    def invalidate_user_cache(self, user_id):
        """Invalidate all cache for a user"""
        pattern = f"user:{user_id}:*"
        return self.delete_pattern(pattern)
    
    def invalidate_course_cache(self, course_id):
        """Invalidate all cache for a course"""
        pattern = f"course:{course_id}:*"
        return self.delete_pattern(pattern)
    
    def get_cache_stats(self):
        """Get cache statistics"""
        if not self.redis_client:
            return {"status": "unavailable"}
        
        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get('used_memory_human', 'N/A'),
                "connected_clients": info.get('connected_clients', 0),
                "total_keys": self.redis_client.dbsize(),
                "hit_rate": info.get('keyspace_hits', 0) / max(info.get('keyspace_misses', 1), 1)
            }
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {"status": "error", "error": str(e)}

# Global instance
cache_service = CacheService()
