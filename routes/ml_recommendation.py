"""
ML Recommendation Engine - Advanced Hybrid Filtering for Course Recommendations
Uses SVD matrix factorization, user embeddings, and hybrid filtering (content-based + collaborative)
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class HybridRecommendationEngine:
    """
    Advanced Hybrid Recommendation System
    
    Implements:
    1. SVD Matrix Factorization for latent factor discovery
    2. User embeddings for deep personalization
    3. Hybrid filtering (Content-based + Collaborative)
    4. Multiple recommendation strategies with weighted fusion
    """
    
    def __init__(self, n_factors=50, n_components=20):
        """
        Initialize the hybrid recommendation engine
        
        Args:
            n_factors: Number of latent factors for SVD
            n_components: Number of components for user embeddings
        """
        self.n_factors = n_factors
        self.n_components = n_components
        
        # Core matrices
        self.user_course_matrix = None
        self.user_ids = []
        self.course_ids = []
        self.user_index_map = {}
        self.course_index_map = {}
        
        # SVD components
        self.svd = None
        self.user_factors = None
        self.course_factors = None
        
        # User embeddings
        self.user_embeddings = None
        self.user_similarity = None
        
        # Course features for content-based filtering
        self.course_features = None
        self.course_feature_matrix = None
        self.course_similarity = None
        
        # Scalers
        self.scaler = StandardScaler()
        
        self.is_fitted = False
        
    def fit(self, enrollments_data, course_metadata=None):
        """
        Fit the hybrid recommendation model on enrollment data
        
        Args:
            enrollments_data: List of dicts with 'user_id', 'course_id', 'progress_percent'
            course_metadata: Optional dict with course features (category, level, description, etc.)
        """
        try:
            if not enrollments_data:
                logger.warning("No enrollment data provided for training")
                return False
            
            # Create DataFrame
            df = pd.DataFrame(enrollments_data)
            
            # Create user-course matrix with progress as implicit rating
            self.user_course_matrix = df.pivot_table(
                index='user_id',
                columns='course_id',
                values='progress_percent',
                fill_value=0
            )
            
            # Store mappings
            self.user_ids = list(self.user_course_matrix.index)
            self.course_ids = list(self.user_course_matrix.columns)
            self.user_index_map = {uid: idx for idx, uid in enumerate(self.user_ids)}
            self.course_index_map = {cid: idx for idx, cid in enumerate(self.course_ids)}
            
            # Fit SVD for matrix factorization
            self._fit_svd()
            
            # Create user embeddings
            self._create_user_embeddings()
            
            # Fit content-based filtering if course metadata available
            if course_metadata:
                self._fit_content_based(course_metadata)
            
            self.is_fitted = True
            logger.info(f"Hybrid recommendation engine fitted with {len(self.user_ids)} users and {len(self.course_ids)} courses")
            return True
            
        except Exception as e:
            logger.error(f"Error fitting hybrid recommendation engine: {str(e)}")
            return False
    
    def _fit_svd(self):
        """Fit SVD for matrix factorization"""
        try:
            # Get the user-course matrix
            matrix = self.user_course_matrix.values
            
            # Fit SVD
            self.svd = TruncatedSVD(n_components=self.n_factors, random_state=42)
            self.user_factors = self.svd.fit_transform(matrix)
            self.course_factors = self.svd.components_.T
            
            logger.info(f"SVD fitted with {self.n_factors} latent factors")
            
        except Exception as e:
            logger.error(f"Error fitting SVD: {str(e)}")
            raise
    
    def _create_user_embeddings(self):
        """Create user embeddings from SVD factors and user behavior"""
        try:
            # User embeddings from SVD factors
            user_svd_embeddings = self.user_factors
            
            # Additional user behavior features
            user_behavior = []
            for user_id in self.user_ids:
                user_idx = self.user_index_map[user_id]
                user_row = self.user_course_matrix.iloc[user_idx]
                
                # Calculate user behavior metrics
                enrolled_courses = (user_row > 0).sum()
                avg_progress = user_row[user_row > 0].mean() if enrolled_courses > 0 else 0
                max_progress = user_row.max()
                total_progress = user_row.sum()
                
                user_behavior.append([
                    enrolled_courses,
                    avg_progress,
                    max_progress,
                    total_progress
                ])
            
            user_behavior = np.array(user_behavior)
            
            # Normalize behavior features
            user_behavior_normalized = self.scaler.fit_transform(user_behavior)
            
            # Combine SVD embeddings with behavior features
            self.user_embeddings = np.hstack([user_svd_embeddings, user_behavior_normalized])
            
            # Calculate user similarity from embeddings
            self.user_similarity = cosine_similarity(self.user_embeddings)
            
            logger.info(f"User embeddings created with shape {self.user_embeddings.shape}")
            
        except Exception as e:
            logger.error(f"Error creating user embeddings: {str(e)}")
            raise
    
    def _fit_content_based(self, course_metadata):
        """Fit content-based filtering using course features"""
        try:
            # Create course feature vectors
            course_features_list = []
            
            for course_id in self.course_ids:
                if course_id in course_metadata:
                    metadata = course_metadata[course_id]
                    
                    # Combine text features
                    text_features = []
                    if 'category' in metadata:
                        text_features.append(metadata['category'])
                    if 'level' in metadata:
                        text_features.append(metadata['level'])
                    if 'description' in metadata:
                        text_features.append(metadata['description'])
                    if 'tags' in metadata:
                        text_features.extend(metadata['tags'])
                    
                    course_features_list.append(' '.join(text_features))
                else:
                    course_features_list.append('')
            
            # Create TF-IDF features
            tfidf = TfidfVectorizer(max_features=100, stop_words='english')
            self.course_feature_matrix = tfidf.fit_transform(course_features_list).toarray()
            
            # Calculate course similarity from features
            self.course_similarity = cosine_similarity(self.course_feature_matrix)
            
            logger.info(f"Content-based filtering fitted with {len(course_metadata)} courses")
            
        except Exception as e:
            logger.error(f"Error fitting content-based filtering: {str(e)}")
            # Don't raise - content-based is optional
    
    def get_svd_recommendations(self, user_id, n_recommendations=6, exclude_enrolled=True):
        """
        Get recommendations using SVD matrix factorization
        
        Args:
            user_id: User ID to get recommendations for
            n_recommendations: Number of recommendations to return
            exclude_enrolled: Whether to exclude already enrolled courses
            
        Returns:
            List of recommended course IDs with scores
        """
        if not self.is_fitted:
            logger.warning("Model not fitted yet")
            return []
        
        if user_id not in self.user_index_map:
            logger.warning(f"User {user_id} not found in training data")
            return []
        
        try:
            user_idx = self.user_index_map[user_id]
            
            # Get user factors
            user_factor = self.user_factors[user_idx]
            
            # Calculate predicted scores for all courses
            predicted_scores = np.dot(user_factor, self.course_factors.T)
            
            # Get enrolled courses
            enrolled_courses = set()
            if exclude_enrolled:
                user_row = self.user_course_matrix.iloc[user_idx]
                enrolled_courses = set(self.course_ids[i] for i, progress in enumerate(user_row) if progress > 0)
            
            # Create course-score pairs
            course_scores = []
            for i, course_id in enumerate(self.course_ids):
                if exclude_enrolled and course_id in enrolled_courses:
                    continue
                course_scores.append({
                    'course_id': course_id,
                    'score': float(predicted_scores[i])
                })
            
            # Sort by score and return top N
            course_scores.sort(key=lambda x: x['score'], reverse=True)
            return course_scores[:n_recommendations]
            
        except Exception as e:
            logger.error(f"Error getting SVD recommendations: {str(e)}")
            return []
    
    def get_embedding_based_recommendations(self, user_id, n_recommendations=6, exclude_enrolled=True):
        """
        Get recommendations using user embeddings
        
        Args:
            user_id: User ID to get recommendations for
            n_recommendations: Number of recommendations to return
            exclude_enrolled: Whether to exclude already enrolled courses
            
        Returns:
            List of recommended course IDs with scores
        """
        if not self.is_fitted:
            logger.warning("Model not fitted yet")
            return []
        
        if user_id not in self.user_index_map:
            logger.warning(f"User {user_id} not found in training data")
            return []
        
        try:
            user_idx = self.user_index_map[user_id]
            
            # Get similarity scores for this user with all other users
            user_similarities = self.user_similarity[user_idx]
            
            # Get top similar users (excluding the user itself)
            similar_users_indices = np.argsort(user_similarities)[::-1][1:11]  # Top 10 similar users
            
            # Get courses enrolled by similar users
            user_courses = set(self.user_course_matrix.columns[self.user_course_matrix.iloc[user_idx] > 0])
            
            # Calculate weighted scores for courses
            course_scores = defaultdict(float)
            for similar_user_idx in similar_users_indices:
                similarity_score = user_similarities[similar_user_idx]
                
                # Get courses enrolled by similar user
                similar_user_courses = self.user_course_matrix.iloc[similar_user_idx]
                
                for course_id in self.course_ids:
                    course_idx = self.course_index_map[course_id]
                    progress = similar_user_courses.iloc[course_idx]
                    
                    # Only consider courses with some progress
                    if progress > 0:
                        # Exclude already enrolled courses if requested
                        if exclude_enrolled and course_id in user_courses:
                            continue
                        
                        # Weight by similarity and progress
                        course_scores[course_id] += similarity_score * (progress / 100.0)
            
            # Sort by score and return top N
            sorted_courses = sorted(course_scores.items(), key=lambda x: x[1], reverse=True)
            
            return [
                {'course_id': course_id, 'score': float(score)}
                for course_id, score in sorted_courses[:n_recommendations]
            ]
            
        except Exception as e:
            logger.error(f"Error getting embedding-based recommendations: {str(e)}")
            return []
    
    def get_content_based_recommendations(self, user_id, n_recommendations=6, exclude_enrolled=True):
        """
        Get recommendations using content-based filtering
        
        Args:
            user_id: User ID to get recommendations for
            n_recommendations: Number of recommendations to return
            exclude_enrolled: Whether to exclude already enrolled courses
            
        Returns:
            List of recommended course IDs with scores
        """
        if not self.is_fitted or self.course_similarity is None:
            logger.warning("Content-based model not fitted yet")
            return []
        
        if user_id not in self.user_index_map:
            logger.warning(f"User {user_id} not found in training data")
            return []
        
        try:
            user_idx = self.user_index_map[user_id]
            
            # Get courses the user has enrolled in
            user_enrollments = self.user_course_matrix.iloc[user_idx]
            enrolled_courses = [
                self.course_ids[i] 
                for i, progress in enumerate(user_enrollments) 
                if progress > 0
            ]
            
            if not enrolled_courses:
                return []
            
            # Calculate scores for unenrolled courses based on similarity to enrolled courses
            course_scores = defaultdict(float)
            
            for enrolled_course in enrolled_courses:
                if enrolled_course not in self.course_index_map:
                    continue
                    
                enrolled_idx = self.course_index_map[enrolled_course]
                
                # Get similarity scores for this course with all other courses
                course_similarities = self.course_similarity[enrolled_idx]
                
                for course_id in self.course_ids:
                    if exclude_enrolled and course_id in enrolled_courses:
                        continue
                    
                    course_idx = self.course_index_map[course_id]
                    similarity = course_similarities[course_idx]
                    
                    # Weight by user's progress in the enrolled course
                    user_progress = user_enrollments.iloc[enrolled_idx] / 100.0
                    course_scores[course_id] += similarity * user_progress
            
            # Sort by score and return top N
            sorted_courses = sorted(course_scores.items(), key=lambda x: x[1], reverse=True)
            
            return [
                {'course_id': course_id, 'score': float(score)}
                for course_id, score in sorted_courses[:n_recommendations]
            ]
            
        except Exception as e:
            logger.error(f"Error getting content-based recommendations: {str(e)}")
            return []
    
    def get_hybrid_recommendations(self, user_id, n_recommendations=6, exclude_enrolled=True,
                                   svd_weight=0.4, embedding_weight=0.3, content_weight=0.3):
        """
        Get recommendations using hybrid approach (SVD + Embeddings + Content-based)
        
        Args:
            user_id: User ID to get recommendations for
            n_recommendations: Number of recommendations to return
            exclude_enrolled: Whether to exclude already enrolled courses
            svd_weight: Weight for SVD recommendations (0-1)
            embedding_weight: Weight for embedding-based recommendations (0-1)
            content_weight: Weight for content-based recommendations (0-1)
            
        Returns:
            List of recommended course IDs with scores
        """
        try:
            # Get recommendations from all methods
            svd_recs = self.get_svd_recommendations(
                user_id, n_recommendations=n_recommendations*2, exclude_enrolled=exclude_enrolled
            )
            embedding_recs = self.get_embedding_based_recommendations(
                user_id, n_recommendations=n_recommendations*2, exclude_enrolled=exclude_enrolled
            )
            content_recs = self.get_content_based_recommendations(
                user_id, n_recommendations=n_recommendations*2, exclude_enrolled=exclude_enrolled
            )
            
            # Combine scores
            combined_scores = defaultdict(float)
            
            for rec in svd_recs:
                combined_scores[rec['course_id']] += rec['score'] * svd_weight
            
            for rec in embedding_recs:
                combined_scores[rec['course_id']] += rec['score'] * embedding_weight
            
            for rec in content_recs:
                combined_scores[rec['course_id']] += rec['score'] * content_weight
            
            # Sort by combined score and return top N
            sorted_courses = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
            
            return [
                {'course_id': course_id, 'score': float(score)}
                for course_id, score in sorted_courses[:n_recommendations]
            ]
            
        except Exception as e:
            logger.error(f"Error getting hybrid recommendations: {str(e)}")
            return []
    
    def get_popular_courses(self, n_recommendations=6):
        """
        Get popular courses as fallback when no user data is available
        
        Args:
            n_recommendations: Number of recommendations to return
            
        Returns:
            List of popular course IDs
        """
        if not self.is_fitted:
            return []
        
        try:
            # Calculate popularity based on enrollment count and average progress
            course_popularity = []
            
            for course_id in self.course_ids:
                course_idx = self.course_index_map[course_id]
                course_column = self.user_course_matrix.iloc[:, course_idx]
                
                # Count enrollments (non-zero progress)
                enrollment_count = (course_column > 0).sum()
                
                # Average progress
                avg_progress = course_column[course_column > 0].mean() if enrollment_count > 0 else 0
                
                # Popularity score: combination of enrollment count and average progress
                popularity_score = enrollment_count * 0.7 + (avg_progress / 100.0) * 0.3
                
                course_popularity.append({
                    'course_id': course_id,
                    'enrollment_count': int(enrollment_count),
                    'avg_progress': float(avg_progress),
                    'popularity_score': float(popularity_score)
                })
            
            # Sort by popularity score
            sorted_courses = sorted(course_popularity, key=lambda x: x['popularity_score'], reverse=True)
            
            return sorted_courses[:n_recommendations]
            
        except Exception as e:
            logger.error(f"Error getting popular courses: {str(e)}")
            return []
    
    def get_similar_courses(self, course_id, n_similar=5):
        """
        Get courses similar to a given course
        
        Args:
            course_id: Course ID to find similar courses for
            n_similar: Number of similar courses to return
            
        Returns:
            List of similar course IDs with similarity scores
        """
        if not self.is_fitted:
            return []
        
        if course_id not in self.course_index_map:
            return []
        
        try:
            course_idx = self.course_index_map[course_id]
            
            # Get similarity scores from course factors (SVD-based)
            course_factor = self.course_factors[course_idx]
            similarities = cosine_similarity([course_factor], self.course_factors)[0]
            
            # Get top similar courses (excluding the course itself)
            similar_indices = np.argsort(similarities)[::-1][1:n_similar+1]
            
            return [
                {
                    'course_id': self.course_ids[idx],
                    'similarity_score': float(similarities[idx])
                }
                for idx in similar_indices
            ]
            
        except Exception as e:
            logger.error(f"Error getting similar courses: {str(e)}")
            return []
    
    def get_user_profile(self, user_id):
        """
        Get user profile with embeddings and preferences
        
        Args:
            user_id: User ID to get profile for
            
        Returns:
            Dict with user profile information
        """
        if not self.is_fitted or user_id not in self.user_index_map:
            return {}
        
        try:
            user_idx = self.user_index_map[user_id]
            user_row = self.user_course_matrix.iloc[user_idx]
            
            # Get enrolled courses
            enrolled_courses = []
            for i, course_id in enumerate(self.course_ids):
                progress = user_row.iloc[i]
                if progress > 0:
                    enrolled_courses.append({
                        'course_id': course_id,
                        'progress': float(progress)
                    })
            
            # Get user embedding
            user_embedding = self.user_embeddings[user_idx].tolist()
            
            return {
                'user_id': user_id,
                'enrolled_courses': enrolled_courses,
                'total_courses': len(enrolled_courses),
                'avg_progress': float(user_row[user_row > 0].mean()) if len(enrolled_courses) > 0 else 0,
                'embedding_dimensions': len(user_embedding),
                'embedding_sample': user_embedding[:5]  # First 5 dimensions as sample
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return {}


# Global instance
recommender = HybridRecommendationEngine()


def train_recommender(enrollments_data, course_metadata=None):
    """
    Train the recommender system with enrollment data
    
    Args:
        enrollments_data: List of dicts with 'user_id', 'course_id', 'progress_percent'
        course_metadata: Optional dict with course features
    
    Returns:
        bool: True if training successful, False otherwise
    """
    return recommender.fit(enrollments_data, course_metadata)


def get_ml_recommendations(user_id, n_recommendations=6, method='hybrid'):
    """
    Get ML-based course recommendations for a user
    
    Args:
        user_id: User ID to get recommendations for
        n_recommendations: Number of recommendations to return
        method: Recommendation method ('svd', 'embedding', 'content', 'hybrid')
    
    Returns:
        List of recommended course IDs with scores
    """
    if method == 'svd':
        return recommender.get_svd_recommendations(user_id, n_recommendations)
    elif method == 'embedding':
        return recommender.get_embedding_based_recommendations(user_id, n_recommendations)
    elif method == 'content':
        return recommender.get_content_based_recommendations(user_id, n_recommendations)
    else:  # hybrid
        return recommender.get_hybrid_recommendations(user_id, n_recommendations)


def get_popular_courses(n_recommendations=6):
    """
    Get popular courses as fallback
    
    Args:
        n_recommendations: Number of recommendations to return
    
    Returns:
        List of popular courses
    """
    return recommender.get_popular_courses(n_recommendations)


def get_similar_courses(course_id, n_similar=5):
    """
    Get courses similar to a given course
    
    Args:
        course_id: Course ID to find similar courses for
        n_similar: Number of similar courses to return
    
    Returns:
        List of similar courses with scores
    """
    return recommender.get_similar_courses(course_id, n_similar)


def get_user_profile(user_id):
    """
    Get user profile with embeddings and preferences
    
    Args:
        user_id: User ID to get profile for
    
    Returns:
        Dict with user profile information
    """
    return recommender.get_user_profile(user_id)
