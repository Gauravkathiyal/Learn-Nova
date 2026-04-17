"""
ML Study Planner Engine - Intelligent Study Schedule Generation
Uses constraint-based scheduling with greedy optimization
"""

import numpy as np
from collections import defaultdict
from datetime import datetime, time, timedelta
import logging

logger = logging.getLogger(__name__)


class ConstraintBasedScheduler:
    """
    Constraint-based Study Scheduler
    
    Uses greedy algorithm with constraints to create optimal study schedules.
    Considers: time slots, deadlines, difficulty weights, and user preferences.
    """
    
    def __init__(self):
        self.user_study_patterns = {}
        self.topic_metadata = {}
        self.is_fitted = False
        
    def fit(self, user_study_data, topic_metadata):
        """
        Fit the scheduler on user study data
        
        Args:
            user_study_data: List of dicts with 'user_id', 'topic', 'study_time', 'completion_rate', 'preferred_time', 'day_of_week'
            topic_metadata: Dict with topic information including difficulty, estimated_time, deadline
        """
        try:
            if not user_study_data:
                logger.warning("No user study data provided for training")
                return False
            
            # Store topic metadata with difficulty weights
            self.topic_metadata = topic_metadata
            
            # Analyze user study patterns
            user_patterns = defaultdict(lambda: {
                'total_time': 0,
                'total_completion': 0,
                'count': 0,
                'preferred_times': [],
                'preferred_days': []
            })
            
            for record in user_study_data:
                user_id = record.get('user_id')
                user_patterns[user_id]['total_time'] += record.get('study_time', 0)
                user_patterns[user_id]['total_completion'] += record.get('completion_rate', 0)
                user_patterns[user_id]['count'] += 1
                user_patterns[user_id]['preferred_times'].append(record.get('preferred_time', 'morning'))
                user_patterns[user_id]['preferred_days'].append(record.get('day_of_week', 0))
            
            # Calculate averages and preferences
            for user_id, pattern in user_patterns.items():
                count = pattern['count']
                self.user_study_patterns[user_id] = {
                    'avg_study_time': pattern['total_time'] / count if count > 0 else 2,
                    'avg_completion': pattern['total_completion'] / count if count > 0 else 70,
                    'preferred_time': max(set(pattern['preferred_times']), key=pattern['preferred_times'].count) if pattern['preferred_times'] else 'morning',
                    'preferred_days': list(set(pattern['preferred_days']))[:3] if pattern['preferred_days'] else [0, 2, 4]
                }
            
            self.is_fitted = True
            logger.info(f"Constraint-based scheduler fitted with {len(user_patterns)} users")
            return True
            
        except Exception as e:
            logger.error(f"Error fitting scheduler: {str(e)}")
            return False
    
    def generate_timetable(self, target_exam, study_hours, user_id=None, deadline=None, difficulty_weights=None):
        """
        Generate a personalized study timetable using constraint-based scheduling
        
        Args:
            target_exam: Target exam or career goal
            study_hours: Available study hours per day
            user_id: Optional user ID for personalization
            deadline: Optional deadline date for the exam
            difficulty_weights: Optional dict of topic -> weight (1-5)
            
        Returns:
            Dict with timetable items
        """
        try:
            # Get topics for the target exam
            topics = self._get_topics_for_exam(target_exam)
            
            if not topics:
                return self._generate_fallback_timetable(target_exam, study_hours)
            
            # Apply difficulty weights
            if difficulty_weights:
                for topic in topics:
                    if topic in difficulty_weights:
                        if topic not in self.topic_metadata:
                            self.topic_metadata[topic] = {}
                        self.topic_metadata[topic]['difficulty_weight'] = difficulty_weights[topic]
            
            # Calculate time allocation using constraint-based approach
            time_allocation = self._calculate_constrained_allocation(
                topics, study_hours, user_id, deadline
            )
            
            # Generate timetable items with time slots
            timetable_items = self._create_constrained_timetable(
                time_allocation, study_hours, user_id, deadline
            )
            
            return {
                'target_exam': target_exam,
                'study_hours_per_day': study_hours,
                'total_topics': len(topics),
                'timetable_items': timetable_items,
                'generated_by_ml': True,
                'deadline': deadline,
                'difficulty_weights': difficulty_weights or {}
            }
            
        except Exception as e:
            logger.error(f"Error generating timetable: {str(e)}")
            return self._generate_fallback_timetable(target_exam, study_hours)
    
    def _get_topics_for_exam(self, target_exam):
        """Get topics for a specific exam with difficulty weights"""
        exam_topics = {
            'UPSC': [
                {'name': 'Indian History', 'difficulty': 4, 'estimated_hours': 20},
                {'name': 'World History', 'difficulty': 3, 'estimated_hours': 15},
                {'name': 'Geography (Physical)', 'difficulty': 3, 'estimated_hours': 12},
                {'name': 'Geography (Indian)', 'difficulty': 3, 'estimated_hours': 12},
                {'name': 'Polity & Constitution', 'difficulty': 4, 'estimated_hours': 18},
                {'name': 'Economy (Basic)', 'difficulty': 3, 'estimated_hours': 10},
                {'name': 'Economy (Current)', 'difficulty': 2, 'estimated_hours': 8},
                {'name': 'Science & Technology', 'difficulty': 3, 'estimated_hours': 12},
                {'name': 'Environment & Ecology', 'difficulty': 3, 'estimated_hours': 10},
                {'name': 'Current Affairs', 'difficulty': 2, 'estimated_hours': 15}
            ],
            'Web Development': [
                {'name': 'HTML5 & CSS3 Fundamentals', 'difficulty': 2, 'estimated_hours': 15},
                {'name': 'JavaScript ES6+', 'difficulty': 4, 'estimated_hours': 25},
                {'name': 'DOM Manipulation', 'difficulty': 3, 'estimated_hours': 12},
                {'name': 'React.js Framework', 'difficulty': 4, 'estimated_hours': 30},
                {'name': 'Node.js & Express', 'difficulty': 4, 'estimated_hours': 25},
                {'name': 'RESTful API Design', 'difficulty': 3, 'estimated_hours': 15},
                {'name': 'Database (MongoDB/SQL)', 'difficulty': 3, 'estimated_hours': 20},
                {'name': 'Authentication & JWT', 'difficulty': 3, 'estimated_hours': 12},
                {'name': 'Git & Version Control', 'difficulty': 2, 'estimated_hours': 8},
                {'name': 'Deployment', 'difficulty': 3, 'estimated_hours': 10}
            ],
            'Data Science': [
                {'name': 'Python Programming', 'difficulty': 3, 'estimated_hours': 20},
                {'name': 'NumPy & Pandas', 'difficulty': 3, 'estimated_hours': 18},
                {'name': 'Data Visualization', 'difficulty': 2, 'estimated_hours': 12},
                {'name': 'Statistics & Probability', 'difficulty': 4, 'estimated_hours': 25},
                {'name': 'Machine Learning Basics', 'difficulty': 4, 'estimated_hours': 30},
                {'name': 'Scikit-Learn', 'difficulty': 3, 'estimated_hours': 15},
                {'name': 'Deep Learning Basics', 'difficulty': 5, 'estimated_hours': 35},
                {'name': 'NLP Fundamentals', 'difficulty': 4, 'estimated_hours': 20},
                {'name': 'Data Preprocessing', 'difficulty': 2, 'estimated_hours': 10},
                {'name': 'ML Projects', 'difficulty': 4, 'estimated_hours': 25}
            ],
            'Machine Learning': [
                {'name': 'Python & Math Refresher', 'difficulty': 2, 'estimated_hours': 15},
                {'name': 'Linear Algebra', 'difficulty': 4, 'estimated_hours': 20},
                {'name': 'Statistics', 'difficulty': 4, 'estimated_hours': 20},
                {'name': 'Supervised Learning', 'difficulty': 4, 'estimated_hours': 30},
                {'name': 'Unsupervised Learning', 'difficulty': 4, 'estimated_hours': 25},
                {'name': 'Neural Networks', 'difficulty': 5, 'estimated_hours': 35},
                {'name': 'TensorFlow/PyTorch', 'difficulty': 4, 'estimated_hours': 30},
                {'name': 'Computer Vision', 'difficulty': 5, 'estimated_hours': 30},
                {'name': 'NLP Basics', 'difficulty': 4, 'estimated_hours': 25},
                {'name': 'ML Projects', 'difficulty': 4, 'estimated_hours': 30}
            ],
            'Cyber Security': [
                {'name': 'Network Security Basics', 'difficulty': 3, 'estimated_hours': 15},
                {'name': 'Linux for Security', 'difficulty': 3, 'estimated_hours': 18},
                {'name': 'Python for Security', 'difficulty': 3, 'estimated_hours': 15},
                {'name': 'Ethical Hacking Intro', 'difficulty': 4, 'estimated_hours': 25},
                {'name': 'Penetration Testing', 'difficulty': 5, 'estimated_hours': 35},
                {'name': 'Web Application Security', 'difficulty': 4, 'estimated_hours': 25},
                {'name': 'Cryptography', 'difficulty': 4, 'estimated_hours': 20},
                {'name': 'Security Tools (Nmap, Metasploit)', 'difficulty': 3, 'estimated_hours': 15},
                {'name': 'Incident Response', 'difficulty': 3, 'estimated_hours': 12},
                {'name': 'Cyber Law', 'difficulty': 2, 'estimated_hours': 8}
            ],
            'Cloud Computing': [
                {'name': 'Cloud Computing Intro', 'difficulty': 2, 'estimated_hours': 10},
                {'name': 'AWS Fundamentals', 'difficulty': 3, 'estimated_hours': 20},
                {'name': 'EC2 & S3', 'difficulty': 3, 'estimated_hours': 18},
                {'name': 'VPC & Networking', 'difficulty': 4, 'estimated_hours': 20},
                {'name': 'IAM & Security', 'difficulty': 3, 'estimated_hours': 15},
                {'name': 'Lambda & Serverless', 'difficulty': 4, 'estimated_hours': 20},
                {'name': 'Databases in Cloud', 'difficulty': 3, 'estimated_hours': 15},
                {'name': 'DevOps Basics', 'difficulty': 3, 'estimated_hours': 18},
                {'name': 'Containerization (Docker)', 'difficulty': 4, 'estimated_hours': 22},
                {'name': 'Cloud Projects', 'difficulty': 4, 'estimated_hours': 25}
            ],
            'Placement Prep': [
                {'name': 'Aptitude - Quantitative', 'difficulty': 3, 'estimated_hours': 20},
                {'name': 'Aptitude - Logical', 'difficulty': 3, 'estimated_hours': 18},
                {'name': 'Aptitude - Verbal', 'difficulty': 2, 'estimated_hours': 15},
                {'name': 'DSA - Arrays & Strings', 'difficulty': 3, 'estimated_hours': 20},
                {'name': 'DSA - Linked Lists', 'difficulty': 3, 'estimated_hours': 15},
                {'name': 'DSA - Stacks & Queues', 'difficulty': 3, 'estimated_hours': 15},
                {'name': 'DSA - Trees & Graphs', 'difficulty': 4, 'estimated_hours': 25},
                {'name': 'System Design Basics', 'difficulty': 4, 'estimated_hours': 20},
                {'name': 'HR Interview Prep', 'difficulty': 2, 'estimated_hours': 10},
                {'name': 'Mock Interviews', 'difficulty': 3, 'estimated_hours': 15}
            ]
        }
        
        return exam_topics.get(target_exam, exam_topics.get('Web Development', []))
    
    def _calculate_constrained_allocation(self, topics, study_hours, user_id=None, deadline=None):
        """
        Calculate time allocation using constraint-based greedy algorithm
        
        Constraints:
        1. Total daily study hours limit
        2. Deadline pressure (if provided)
        3. Difficulty weights (harder topics get more time)
        4. User preferences and completion patterns
        """
        allocation = {}
        
        # Get user preferences if available
        user_preferences = None
        if user_id and self.is_fitted:
            user_preferences = self.user_study_patterns.get(user_id)
        
        # Calculate total available time per week
        total_weekly_hours = study_hours * 7
        
        # Calculate deadline pressure factor
        deadline_factor = 1.0
        if deadline:
            try:
                if isinstance(deadline, str):
                    deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
                else:
                    deadline_date = deadline
                
                days_until_deadline = (deadline_date - datetime.now().date()).days
                if days_until_deadline > 0:
                    # More pressure = more time allocation
                    deadline_factor = min(2.0, 30 / max(days_until_deadline, 1))
            except:
                pass
        
        # Calculate total estimated hours needed
        total_estimated_hours = sum(t.get('estimated_hours', 15) for t in topics)
        
        # Greedy allocation: prioritize by difficulty and deadline
        for topic_info in topics:
            topic_name = topic_info['name']
            difficulty = topic_info.get('difficulty', 3)
            estimated_hours = topic_info.get('estimated_hours', 15)
            
            # Base allocation proportional to estimated hours
            base_allocation = (estimated_hours / total_estimated_hours) * total_weekly_hours
            
            # Apply difficulty weight (harder topics get more time)
            difficulty_weight = difficulty / 3.0  # Normalize around 1.0
            
            # Apply deadline pressure
            deadline_weight = deadline_factor
            
            # Apply user preference factor
            user_weight = 1.0
            if user_preferences:
                # Users with higher completion rates get more balanced allocation
                completion_factor = user_preferences.get('avg_completion', 70) / 100.0
                user_weight = 0.8 + 0.4 * completion_factor
            
            # Calculate final allocation
            final_allocation = base_allocation * difficulty_weight * deadline_weight * user_weight
            
            # Cap allocation to prevent over-allocation
            max_allocation = total_weekly_hours / len(topics) * 2.0
            allocation[topic_name] = min(final_allocation, max_allocation)
        
        # Normalize to fit available time
        total_allocated = sum(allocation.values())
        if total_allocated > 0:
            scale_factor = total_weekly_hours / total_allocated
            for topic in allocation:
                allocation[topic] *= scale_factor
        
        return allocation
    
    def _create_constrained_timetable(self, time_allocation, study_hours, user_id=None, deadline=None):
        """
        Create timetable items using constraint-based scheduling
        
        Constraints:
        1. Time slot availability
        2. Topic difficulty ordering (harder topics in morning)
        3. Spaced repetition (don't repeat same topic consecutively)
        4. Weekend mock tests
        """
        items = []
        
        # Define time slots with constraints
        time_slots = self._generate_constrained_time_slots(study_hours)
        
        # Sort topics by difficulty (harder first for morning slots)
        sorted_topics = sorted(
            time_allocation.items(),
            key=lambda x: self._get_topic_difficulty(x[0]),
            reverse=True
        )
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Track topic usage for spaced repetition
        topic_usage = defaultdict(int)
        last_topic_per_day = {}
        
        for day_idx, day in enumerate(days):
            is_weekend = day_idx >= 5
            
            if is_weekend:
                # Weekend: Mock tests and revision
                items.append({
                    'day': day,
                    'start_time': '09:00',
                    'end_time': '12:00',
                    'subject': 'Mock Test Series',
                    'topic': f'Full Length Mock Test - {day}',
                    'is_weekend': True,
                    'difficulty': 4
                })
                
                items.append({
                    'day': day,
                    'start_time': '14:00',
                    'end_time': '16:00',
                    'subject': 'Test Analysis',
                    'topic': f'Mock Test Analysis & Revision - {day}',
                    'is_weekend': True,
                    'difficulty': 3
                })
            else:
                # Weekday: Apply constraint-based scheduling
                available_slots = time_slots.copy()
                
                # Sort slots by time (morning first for harder topics)
                available_slots.sort(key=lambda x: x[0])
                
                for slot_idx, (start_time, end_time) in enumerate(available_slots):
                    # Select topic based on constraints
                    selected_topic = self._select_topic_with_constraints(
                        sorted_topics, topic_usage, last_topic_per_day.get(day_idx - 1), slot_idx
                    )
                    
                    if selected_topic:
                        topic_name, allocation = selected_topic
                        
                        items.append({
                            'day': day,
                            'start_time': start_time,
                            'end_time': end_time,
                            'subject': topic_name,
                            'topic': topic_name,
                            'is_weekend': False,
                            'difficulty': self._get_topic_difficulty(topic_name)
                        })
                        
                        # Update tracking
                        topic_usage[topic_name] += 1
                        last_topic_per_day[day_idx] = topic_name
        
        return items
    
    def _get_topic_difficulty(self, topic_name):
        """Get difficulty level for a topic"""
        # Check in topic metadata
        for topic_info in self.topic_metadata.get('topics', []):
            if isinstance(topic_info, dict) and topic_info.get('name') == topic_name:
                return topic_info.get('difficulty', 3)
        
        # Default difficulty based on topic name keywords
        difficult_keywords = ['advanced', 'deep learning', 'neural networks', 'penetration', 'system design']
        if any(keyword in topic_name.lower() for keyword in difficult_keywords):
            return 5
        
        return 3
    
    def _select_topic_with_constraints(self, sorted_topics, topic_usage, last_topic, slot_idx):
        """
        Select topic using constraint-based greedy approach
        
        Constraints:
        1. Don't repeat same topic consecutively
        2. Prioritize harder topics in morning slots
        3. Balance topic coverage
        """
        if not sorted_topics:
            return None
        
        # Filter out last used topic (spaced repetition)
        available_topics = [
            (topic, alloc) for topic, alloc in sorted_topics
            if topic != last_topic
        ]
        
        if not available_topics:
            available_topics = sorted_topics
        
        # For morning slots (first 2), prioritize harder topics
        if slot_idx < 2:
            # Select from top 3 hardest topics
            candidates = available_topics[:min(3, len(available_topics))]
        else:
            # For afternoon/evening, select from least used topics
            candidates = sorted(
                available_topics,
                key=lambda x: topic_usage.get(str(x[0]), 0)
            )[:min(3, len(available_topics))]
        
        # Select topic with highest allocation from candidates
        if candidates:
            return max(candidates, key=lambda x: x[1])
        
        return available_topics[0] if available_topics else None
    
    def _generate_constrained_time_slots(self, study_hours):
        """Generate time slots with constraints"""
        slots = []
        start_hour = 9  # Start at 9 AM
        
        # Calculate slot duration and gap based on study hours
        if study_hours <= 2:
            slot_duration = 90  # 1.5 hours
            gap = 60  # 1 hour break
        elif study_hours <= 4:
            slot_duration = 90  # 1.5 hours
            gap = 45  # 45 min break
        else:
            slot_duration = 75  # 1.25 hours
            gap = 30  # 30 min break
        
        for i in range(study_hours):
            slot_start = start_hour + (i * (slot_duration + gap) // 60)
            end_hour = slot_start + (slot_duration // 60)
            end_min = slot_duration % 60
            
            if slot_start < 21:  # Don't go past 9 PM
                start_str = f'{slot_start:02d}:00'
                end_str = f'{end_hour:02d}:{end_min:02d}' if end_min else f'{end_hour:02d}:00'
                slots.append((start_str, end_str))
        
        # Ensure at least one time slot
        if not slots:
            slots.append(('09:00', '10:30'))
        
        return slots
    
    def _generate_fallback_timetable(self, target_exam, study_hours):
        """Generate fallback timetable when scheduling fails"""
        topics = self._get_topics_for_exam(target_exam)
        
        items = []
        time_slots = self._generate_constrained_time_slots(study_hours)
        
        topic_idx = 0
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day_idx, day in enumerate(days):
            is_weekend = day_idx >= 5
            
            if is_weekend:
                items.append({
                    'day': day,
                    'start_time': '09:00',
                    'end_time': '12:00',
                    'subject': 'Mock Test Series',
                    'topic': f'Full Length Mock Test - {day}',
                    'is_weekend': True,
                    'difficulty': 4
                })
            else:
                for slot_idx, (start_time, end_time) in enumerate(time_slots):
                    if topic_idx < len(topics):
                        topic = topics[topic_idx]
                        topic_name = topic['name'] if isinstance(topic, dict) else topic
                        
                        items.append({
                            'day': day,
                            'start_time': start_time,
                            'end_time': end_time,
                            'subject': topic_name,
                            'topic': topic_name,
                            'is_weekend': False,
                            'difficulty': topic.get('difficulty', 3) if isinstance(topic, dict) else 3
                        })
                        
                        topic_idx += 1
        
        return {
            'target_exam': target_exam,
            'study_hours_per_day': study_hours,
            'total_topics': len(topics),
            'timetable_items': items,
            'generated_by_ml': False
        }
    
    def get_optimal_study_time(self, topic, user_id=None):
        """Get optimal study time for a topic based on difficulty"""
        if not self.is_fitted:
            return 2  # Default 2 hours
        
        # Find topic in metadata
        for topic_info in self.topic_metadata.get('topics', []):
            if isinstance(topic_info, dict) and topic_info.get('name') == topic:
                estimated_hours = topic_info.get('estimated_hours', 15)
                # Return weekly allocation (divide by 7 for daily)
                return estimated_hours / 7
        
        return 2  # Default
    
    def get_user_study_pattern(self, user_id):
        """Get study pattern for a user"""
        if not self.is_fitted:
            return None
        
        return self.user_study_patterns.get(user_id)


# Global instance
study_planner = ConstraintBasedScheduler()


def train_study_planner(user_study_data, topic_metadata):
    """
    Train the study planner with user study data
    
    Args:
        user_study_data: List of dicts with user study information
        topic_metadata: Dict with topic metadata
        
    Returns:
        bool: True if training successful, False otherwise
    """
    return study_planner.fit(user_study_data, topic_metadata)


def generate_ml_timetable(target_exam, study_hours, user_id=None, deadline=None, difficulty_weights=None):
    """
    Generate constraint-based study timetable
    
    Args:
        target_exam: Target exam or career goal
        study_hours: Available study hours per day
        user_id: Optional user ID for personalization
        deadline: Optional deadline date for the exam
        difficulty_weights: Optional dict of topic -> weight (1-5)
        
    Returns:
        Dict with timetable items
    """
    return study_planner.generate_timetable(target_exam, study_hours, user_id, deadline, difficulty_weights)


def get_optimal_study_time(topic, user_id=None):
    """
    Get optimal study time for a topic
    
    Args:
        topic: Topic name
        user_id: Optional user ID for personalization
        
    Returns:
        float: Recommended study time in hours
    """
    return study_planner.get_optimal_study_time(topic, user_id)


def get_user_study_pattern(user_id):
    """
    Get study pattern for a user
    
    Args:
        user_id: User ID
        
    Returns:
        Dict with user study pattern or None
    """
    return study_planner.get_user_study_pattern(user_id)
