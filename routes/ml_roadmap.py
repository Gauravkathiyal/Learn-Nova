"""
ML Roadmap Engine - Intelligent Study Roadmap Generation
Uses DAG-based topic sequencing with prerequisite mapping
Replaces KMeans clustering with rule-based + ML hybrid approach
"""

import numpy as np
import pandas as pd
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class TopicGraph:
    """
    Directed Acyclic Graph (DAG) for topic prerequisites and sequencing
    """
    
    def __init__(self):
        self.graph = defaultdict(list)  # adjacency list
        self.in_degree = defaultdict(int)
        self.topics = set()
        self.topic_metadata = {}
    
    def add_topic(self, topic: str, metadata: Dict = None):
        """Add a topic to the graph"""
        self.topics.add(topic)
        if metadata:
            self.topic_metadata[topic] = metadata
        if topic not in self.in_degree:
            self.in_degree[topic] = 0
    
    def add_prerequisite(self, prerequisite: str, topic: str):
        """Add a prerequisite relationship: prerequisite must be learned before topic"""
        if prerequisite not in self.topics:
            self.add_topic(prerequisite)
        if topic not in self.topics:
            self.add_topic(topic)
        
        self.graph[prerequisite].append(topic)
        self.in_degree[topic] += 1
    
    def get_prerequisites(self, topic: str) -> List[str]:
        """Get all prerequisites for a topic"""
        prereqs = []
        for prereq, dependents in self.graph.items():
            if topic in dependents:
                prereqs.append(prereq)
        return prereqs
    
    def get_dependents(self, topic: str) -> List[str]:
        """Get all topics that depend on this topic"""
        return self.graph.get(topic, [])
    
    def topological_sort(self) -> List[str]:
        """
        Perform topological sort to get optimal learning sequence
        Uses Kahn's algorithm
        """
        # Calculate in-degrees
        in_degree = {topic: 0 for topic in self.topics}
        for topic in self.topics:
            for dependent in self.graph.get(topic, []):
                in_degree[dependent] += 1
        
        # Initialize queue with topics having no prerequisites
        queue = deque([topic for topic in self.topics if in_degree[topic] == 0])
        result = []
        
        while queue:
            # Sort queue by difficulty to prioritize easier topics
            queue_list = list(queue)
            queue_list.sort(key=lambda t: self.topic_metadata.get(t, {}).get('difficulty', 3))
            queue = deque(queue_list)
            
            topic = queue.popleft()
            result.append(topic)
            
            # Reduce in-degree of dependents
            for dependent in self.graph.get(topic, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check for cycles
        if len(result) != len(self.topics):
            logger.warning("Cycle detected in topic graph! Using fallback ordering.")
            return list(self.topics)
        
        return result
    
    def get_learning_path(self, start_topic: str = None, end_topic: str = None) -> List[str]:
        """Get a learning path from start to end topic"""
        if start_topic and end_topic:
            # BFS to find path
            queue = deque([(start_topic, [start_topic])])
            visited = {start_topic}
            
            while queue:
                topic, path = queue.popleft()
                
                if topic == end_topic:
                    return path
                
                for dependent in self.graph.get(topic, []):
                    if dependent not in visited:
                        visited.add(dependent)
                        queue.append((dependent, path + [dependent]))
            
            return []  # No path found
        
        # Return full topological sort
        return self.topological_sort()


class MLRoadmapGenerator:
    """
    ML-based Roadmap Generator with DAG-based sequencing
    
    Uses rule-based prerequisite mapping combined with ML for difficulty estimation
    to create personalized study roadmaps based on user performance and goals.
    """
    
    def __init__(self):
        self.topic_graph = TopicGraph()
        self.user_performance_data = {}
        self.is_fitted = False
        self._initialize_prerequisite_mappings()
    
    def _initialize_prerequisite_mappings(self):
        """Initialize comprehensive prerequisite mappings for all exam topics"""
        
        # Web Development prerequisites
        web_dev_prereqs = {
            'HTML5 & CSS3 Fundamentals': [],
            'JavaScript ES6+': ['HTML5 & CSS3 Fundamentals'],
            'DOM Manipulation': ['JavaScript ES6+'],
            'React.js Framework': ['JavaScript ES6+', 'DOM Manipulation'],
            'Node.js & Express': ['JavaScript ES6+'],
            'RESTful API Design': ['Node.js & Express'],
            'Database (MongoDB/SQL)': ['HTML5 & CSS3 Fundamentals'],
            'Authentication & JWT': ['Node.js & Express', 'RESTful API Design'],
            'Git & Version Control': ['HTML5 & CSS3 Fundamentals'],
            'Deployment': ['React.js Framework', 'Node.js & Express', 'Database (MongoDB/SQL)']
        }
        
        # Data Science prerequisites
        data_science_prereqs = {
            'Python Programming': [],
            'NumPy & Pandas': ['Python Programming'],
            'Data Visualization': ['Python Programming', 'NumPy & Pandas'],
            'Statistics & Probability': ['Python Programming'],
            'Machine Learning Basics': ['Python Programming', 'NumPy & Pandas', 'Statistics & Probability'],
            'Scikit-Learn': ['Machine Learning Basics'],
            'Deep Learning Basics': ['Machine Learning Basics', 'NumPy & Pandas'],
            'NLP Fundamentals': ['Python Programming', 'Machine Learning Basics'],
            'Data Preprocessing': ['Python Programming', 'NumPy & Pandas'],
            'ML Projects': ['Machine Learning Basics', 'Scikit-Learn', 'Data Preprocessing']
        }
        
        # Machine Learning prerequisites
        ml_prereqs = {
            'Python & Math Refresher': [],
            'Linear Algebra': ['Python & Math Refresher'],
            'Statistics': ['Python & Math Refresher'],
            'Supervised Learning': ['Python & Math Refresher', 'Linear Algebra', 'Statistics'],
            'Unsupervised Learning': ['Supervised Learning'],
            'Neural Networks': ['Supervised Learning', 'Linear Algebra'],
            'TensorFlow/PyTorch': ['Neural Networks', 'Python & Math Refresher'],
            'Computer Vision': ['Neural Networks', 'TensorFlow/PyTorch'],
            'NLP Basics': ['Neural Networks', 'Supervised Learning'],
            'ML Projects': ['Supervised Learning', 'Unsupervised Learning', 'TensorFlow/PyTorch']
        }
        
        # UPSC prerequisites
        upsc_prereqs = {
            'Indian History': [],
            'World History': [],
            'Geography (Physical)': [],
            'Geography (Indian)': ['Geography (Physical)'],
            'Polity & Constitution': ['Indian History'],
            'Economy (Basic)': ['Polity & Constitution'],
            'Economy (Current)': ['Economy (Basic)'],
            'Science & Technology': [],
            'Environment & Ecology': ['Geography (Physical)', 'Science & Technology'],
            'Current Affairs': ['Indian History', 'Polity & Constitution', 'Economy (Basic)']
        }
        
        # Cyber Security prerequisites
        cyber_prereqs = {
            'Network Security Basics': [],
            'Linux for Security': ['Network Security Basics'],
            'Python for Security': ['Network Security Basics'],
            'Ethical Hacking Intro': ['Network Security Basics', 'Linux for Security'],
            'Penetration Testing': ['Ethical Hacking Intro', 'Python for Security'],
            'Web Application Security': ['Ethical Hacking Intro', 'Network Security Basics'],
            'Cryptography': ['Network Security Basics'],
            'Security Tools (Nmap, Metasploit)': ['Ethical Hacking Intro', 'Linux for Security'],
            'Incident Response': ['Network Security Basics', 'Ethical Hacking Intro'],
            'Cyber Law': ['Network Security Basics']
        }
        
        # Cloud Computing prerequisites
        cloud_prereqs = {
            'Cloud Computing Intro': [],
            'AWS Fundamentals': ['Cloud Computing Intro'],
            'EC2 & S3': ['AWS Fundamentals'],
            'VPC & Networking': ['AWS Fundamentals'],
            'IAM & Security': ['AWS Fundamentals'],
            'Lambda & Serverless': ['AWS Fundamentals', 'EC2 & S3'],
            'Databases in Cloud': ['AWS Fundamentals', 'EC2 & S3'],
            'DevOps Basics': ['Cloud Computing Intro', 'AWS Fundamentals'],
            'Containerization (Docker)': ['DevOps Basics', 'Linux for Security'],
            'Cloud Projects': ['EC2 & S3', 'VPC & Networking', 'IAM & Security', 'Lambda & Serverless']
        }
        
        # Placement Prep prerequisites
        placement_prereqs = {
            'Aptitude - Quantitative': [],
            'Aptitude - Logical': [],
            'Aptitude - Verbal': [],
            'DSA - Arrays & Strings': ['Aptitude - Quantitative'],
            'DSA - Linked Lists': ['DSA - Arrays & Strings'],
            'DSA - Stacks & Queues': ['DSA - Arrays & Strings'],
            'DSA - Trees & Graphs': ['DSA - Linked Lists', 'DSA - Stacks & Queues'],
            'System Design Basics': ['DSA - Trees & Graphs'],
            'HR Interview Prep': [],
            'Mock Interviews': ['HR Interview Prep', 'System Design Basics']
        }
        
        # Store all prerequisites
        self.exam_prerequisites = {
            'Web Development': web_dev_prereqs,
            'Data Science': data_science_prereqs,
            'Machine Learning': ml_prereqs,
            'UPSC': upsc_prereqs,
            'Cyber Security': cyber_prereqs,
            'Cloud Computing': cloud_prereqs,
            'Placement Prep': placement_prereqs
        }
        
        # Initialize topic difficulty levels (rule-based)
        self.topic_difficulty_levels = {
            # Web Development
            'HTML5 & CSS3 Fundamentals': 1,
            'JavaScript ES6+': 2,
            'DOM Manipulation': 2,
            'React.js Framework': 3,
            'Node.js & Express': 3,
            'RESTful API Design': 3,
            'Database (MongoDB/SQL)': 2,
            'Authentication & JWT': 4,
            'Git & Version Control': 1,
            'Deployment': 4,
            
            # Data Science
            'Python Programming': 1,
            'NumPy & Pandas': 2,
            'Data Visualization': 2,
            'Statistics & Probability': 2,
            'Machine Learning Basics': 3,
            'Scikit-Learn': 3,
            'Deep Learning Basics': 4,
            'NLP Fundamentals': 4,
            'Data Preprocessing': 2,
            'ML Projects': 5,
            
            # Machine Learning
            'Python & Math Refresher': 1,
            'Linear Algebra': 2,
            'Statistics': 2,
            'Supervised Learning': 3,
            'Unsupervised Learning': 3,
            'Neural Networks': 4,
            'TensorFlow/PyTorch': 4,
            'Computer Vision': 5,
            'NLP Basics': 4,
            'ML Projects': 5,
            
            # UPSC
            'Indian History': 2,
            'World History': 2,
            'Geography (Physical)': 2,
            'Geography (Indian)': 2,
            'Polity & Constitution': 3,
            'Economy (Basic)': 3,
            'Economy (Current)': 4,
            'Science & Technology': 2,
            'Environment & Ecology': 3,
            'Current Affairs': 4,
            
            # Cyber Security
            'Network Security Basics': 1,
            'Linux for Security': 2,
            'Python for Security': 2,
            'Ethical Hacking Intro': 3,
            'Penetration Testing': 4,
            'Web Application Security': 4,
            'Cryptography': 3,
            'Security Tools (Nmap, Metasploit)': 3,
            'Incident Response': 4,
            'Cyber Law': 2,
            
            # Cloud Computing
            'Cloud Computing Intro': 1,
            'AWS Fundamentals': 2,
            'EC2 & S3': 2,
            'VPC & Networking': 3,
            'IAM & Security': 3,
            'Lambda & Serverless': 4,
            'Databases in Cloud': 3,
            'DevOps Basics': 3,
            'Containerization (Docker)': 4,
            'Cloud Projects': 5,
            
            # Placement Prep
            'Aptitude - Quantitative': 1,
            'Aptitude - Logical': 1,
            'Aptitude - Verbal': 1,
            'DSA - Arrays & Strings': 2,
            'DSA - Linked Lists': 2,
            'DSA - Stacks & Queues': 2,
            'DSA - Trees & Graphs': 3,
            'System Design Basics': 4,
            'HR Interview Prep': 1,
            'Mock Interviews': 3
        }
    
    def fit(self, user_progress_data, topic_metadata):
        """
        Fit the roadmap model on user progress data
        
        Args:
            user_progress_data: List of dicts with 'user_id', 'topic', 'completion_rate', 'test_score', 'time_spent'
            topic_metadata: Dict with topic information including difficulty, prerequisites, category
        """
        try:
            if not user_progress_data:
                logger.warning("No user progress data provided for training")
                return False
            
            # Create DataFrame
            df = pd.DataFrame(user_progress_data)
            
            # Calculate topic difficulty based on user performance (ML component)
            topic_stats = df.groupby('topic').agg({
                'completion_rate': 'mean',
                'test_score': 'mean',
                'time_spent': 'mean'
            }).reset_index()
            
            # Update difficulty levels based on user performance
            for _, row in topic_stats.iterrows():
                topic = row['topic']
                completion = row['completion_rate']
                score = row['test_score']
                time_spent = row['time_spent']
                
                # Calculate difficulty adjustment based on performance
                # Lower completion/score and higher time = higher difficulty
                performance_factor = (1 - completion) * 0.4 + (1 - score) * 0.4 + min(time_spent / 10, 1) * 0.2
                
                # Adjust base difficulty
                base_difficulty = self.topic_difficulty_levels.get(topic, 3)
                adjusted_difficulty = base_difficulty + (performance_factor * 2)
                adjusted_difficulty = min(5, max(1, adjusted_difficulty))
                
                self.topic_difficulty_levels[topic] = adjusted_difficulty
            
            # Update topic metadata in graph
            for topic, difficulty in self.topic_difficulty_levels.items():
                self.topic_graph.add_topic(topic, {'difficulty': difficulty})
            
            self.is_fitted = True
            logger.info(f"Roadmap model fitted with {len(topic_stats)} topics")
            return True
            
        except Exception as e:
            logger.error(f"Error fitting roadmap model: {str(e)}")
            return False
    
    def generate_roadmap(self, target_exam, current_level, exam_date, user_id=None):
        """
        Generate a personalized study roadmap using DAG-based sequencing
        
        Args:
            target_exam: Target exam or career goal
            current_level: User's current knowledge level (1-5)
            exam_date: Target exam date
            user_id: Optional user ID for personalization
            
        Returns:
            Dict with roadmap milestones and topics
        """
        try:
            # Get topics and prerequisites for the target exam
            topics = self._get_topics_for_exam(target_exam)
            
            if not topics:
                return self._generate_fallback_roadmap(target_exam)
            
            # Build topic graph with prerequisites
            self._build_topic_graph(target_exam, topics)
            
            # Filter topics based on current level
            suitable_topics = self._filter_topics_by_level(topics, current_level)
            
            # Get optimal learning sequence using topological sort
            sequenced_topics = self._sequence_topics_dag(suitable_topics)
            
            # Generate milestones
            milestones = self._create_milestones(sequenced_topics, exam_date, current_level)
            
            return {
                'target_exam': target_exam,
                'current_level': current_level,
                'total_milestones': len(milestones),
                'milestones': milestones,
                'generated_by_ml': self.is_fitted,
                'sequencing_method': 'DAG_topological_sort'
            }
            
        except Exception as e:
            logger.error(f"Error generating roadmap: {str(e)}")
            return self._generate_fallback_roadmap(target_exam)
    
    def _get_topics_for_exam(self, target_exam):
        """Get topics for a specific exam"""
        exam_topics = {
            'UPSC': [
                'Indian History', 'World History', 'Geography (Physical)', 'Geography (Indian)',
                'Polity & Constitution', 'Economy (Basic)', 'Economy (Current)',
                'Science & Technology', 'Environment & Ecology', 'Current Affairs'
            ],
            'Web Development': [
                'HTML5 & CSS3 Fundamentals', 'JavaScript ES6+', 'DOM Manipulation',
                'React.js Framework', 'Node.js & Express', 'RESTful API Design',
                'Database (MongoDB/SQL)', 'Authentication & JWT', 'Git & Version Control', 'Deployment'
            ],
            'Data Science': [
                'Python Programming', 'NumPy & Pandas', 'Data Visualization',
                'Statistics & Probability', 'Machine Learning Basics', 'Scikit-Learn',
                'Deep Learning Basics', 'NLP Fundamentals', 'Data Preprocessing', 'ML Projects'
            ],
            'Machine Learning': [
                'Python & Math Refresher', 'Linear Algebra', 'Statistics',
                'Supervised Learning', 'Unsupervised Learning', 'Neural Networks',
                'TensorFlow/PyTorch', 'Computer Vision', 'NLP Basics', 'ML Projects'
            ],
            'Cyber Security': [
                'Network Security Basics', 'Linux for Security', 'Python for Security',
                'Ethical Hacking Intro', 'Penetration Testing', 'Web Application Security',
                'Cryptography', 'Security Tools (Nmap, Metasploit)', 'Incident Response', 'Cyber Law'
            ],
            'Cloud Computing': [
                'Cloud Computing Intro', 'AWS Fundamentals', 'EC2 & S3',
                'VPC & Networking', 'IAM & Security', 'Lambda & Serverless',
                'Databases in Cloud', 'DevOps Basics', 'Containerization (Docker)', 'Cloud Projects'
            ],
            'Placement Prep': [
                'Aptitude - Quantitative', 'Aptitude - Logical', 'Aptitude - Verbal',
                'DSA - Arrays & Strings', 'DSA - Linked Lists', 'DSA - Stacks & Queues',
                'DSA - Trees & Graphs', 'System Design Basics', 'HR Interview Prep', 'Mock Interviews'
            ]
        }
        
        return exam_topics.get(target_exam, exam_topics.get('Web Development', []))
    
    def _build_topic_graph(self, target_exam, topics):
        """Build the topic graph with prerequisites for a specific exam"""
        # Clear existing graph
        self.topic_graph = TopicGraph()
        
        # Get prerequisites for this exam
        prereqs = self.exam_prerequisites.get(target_exam, {})
        
        # Add topics to graph
        for topic in topics:
            difficulty = self.topic_difficulty_levels.get(topic, 3)
            self.topic_graph.add_topic(topic, {'difficulty': difficulty})
        
        # Add prerequisite relationships
        for topic in topics:
            topic_prereqs = prereqs.get(topic, [])
            for prereq in topic_prereqs:
                if prereq in topics:  # Only add if prerequisite is in the topic list
                    self.topic_graph.add_prerequisite(prereq, topic)
    
    def _filter_topics_by_level(self, topics, current_level):
        """Filter topics based on user's current level"""
        filtered = []
        for topic in topics:
            difficulty = self.topic_difficulty_levels.get(topic, 3)
            # Include topics that are at or slightly above current level
            if difficulty >= current_level and difficulty <= current_level + 2:
                filtered.append(topic)
        
        return filtered if filtered else topics
    
    def _sequence_topics_dag(self, topics):
        """
        Sequence topics using DAG topological sort
        This ensures prerequisites are learned before dependent topics
        """
        # Create a subgraph with only the selected topics
        subgraph = TopicGraph()
        
        for topic in topics:
            difficulty = self.topic_difficulty_levels.get(topic, 3)
            subgraph.add_topic(topic, {'difficulty': difficulty})
        
        # Add prerequisite relationships from the main graph
        for topic in topics:
            prereqs = self.topic_graph.get_prerequisites(topic)
            for prereq in prereqs:
                if prereq in topics:
                    subgraph.add_prerequisite(prereq, topic)
        
        # Perform topological sort
        return subgraph.topological_sort()
    
    def _create_milestones(self, topics, exam_date, current_level):
        """Create milestones from sequenced topics"""
        milestones = []
        
        # Group topics into milestones (3-4 topics per milestone)
        topics_per_milestone = 3
        for i in range(0, len(topics), topics_per_milestone):
            milestone_topics = topics[i:i+topics_per_milestone]
            
            # Calculate milestone difficulty
            avg_difficulty = np.mean([
                self.topic_difficulty_levels.get(t, 3)
                for t in milestone_topics
            ])
            
            # Calculate estimated duration (in weeks)
            estimated_weeks = len(milestone_topics) * 2  # 2 weeks per topic
            
            # Get prerequisites for this milestone
            milestone_prereqs = set()
            for topic in milestone_topics:
                prereqs = self.topic_graph.get_prerequisites(topic)
                for prereq in prereqs:
                    if prereq not in milestone_topics:
                        milestone_prereqs.add(prereq)
            
            milestone = {
                'milestone_number': len(milestones) + 1,
                'topics': milestone_topics,
                'difficulty_level': min(5, max(1, int(avg_difficulty))),
                'estimated_weeks': estimated_weeks,
                'prerequisites': list(milestone_prereqs),
                'description': f'Milestone {len(milestones) + 1}: Master {", ".join(milestone_topics[:2])} and more'
            }
            
            milestones.append(milestone)
        
        return milestones
    
    def _generate_fallback_roadmap(self, target_exam):
        """Generate fallback roadmap when ML is not available"""
        topics = self._get_topics_for_exam(target_exam)
        
        milestones = []
        topics_per_milestone = 3
        
        for i in range(0, len(topics), topics_per_milestone):
            milestone_topics = topics[i:i+topics_per_milestone]
            
            milestone = {
                'milestone_number': len(milestones) + 1,
                'topics': milestone_topics,
                'difficulty_level': 3,
                'estimated_weeks': len(milestone_topics) * 2,
                'prerequisites': [],
                'description': f'Milestone {len(milestones) + 1}: Learn {", ".join(milestone_topics[:2])}'
            }
            
            milestones.append(milestone)
        
        return {
            'target_exam': target_exam,
            'current_level': 3,
            'total_milestones': len(milestones),
            'milestones': milestones,
            'generated_by_ml': False,
            'sequencing_method': 'fallback'
        }
    
    def get_topic_difficulty(self, topic):
        """Get difficulty level for a topic"""
        return self.topic_difficulty_levels.get(topic, 3)
    
    def get_recommended_study_time(self, topic, user_level):
        """Get recommended study time for a topic based on user level"""
        topic_difficulty = self.topic_difficulty_levels.get(topic, 3)
        
        # Calculate study time based on difficulty and user level
        difficulty_gap = max(0, topic_difficulty - user_level)
        base_time = 2  # Base 2 hours
        additional_time = difficulty_gap * 0.5  # Add 0.5 hours per difficulty level gap
        
        return base_time + additional_time
    
    def get_prerequisite_chain(self, topic):
        """Get the full prerequisite chain for a topic"""
        chain = []
        visited = set()
        
        def dfs(current_topic):
            if current_topic in visited:
                return
            visited.add(current_topic)
            
            prereqs = self.topic_graph.get_prerequisites(current_topic)
            for prereq in prereqs:
                dfs(prereq)
            
            chain.append(current_topic)
        
        dfs(topic)
        return chain
    
    def get_learning_path_visualization(self, target_exam):
        """Get a visualization-ready representation of the learning path"""
        topics = self._get_topics_for_exam(target_exam)
        self._build_topic_graph(target_exam, topics)
        
        # Get topological order
        ordered_topics = self.topic_graph.topological_sort()
        
        # Build visualization data
        nodes = []
        edges = []
        
        for i, topic in enumerate(ordered_topics):
            difficulty = self.topic_difficulty_levels.get(topic, 3)
            nodes.append({
                'id': topic,
                'label': topic,
                'level': difficulty,
                'order': i + 1
            })
        
        # Add edges for prerequisites
        for topic in ordered_topics:
            prereqs = self.topic_graph.get_prerequisites(topic)
            for prereq in prereqs:
                edges.append({
                    'from': prereq,
                    'to': topic
                })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'exam': target_exam
        }


# Global instance
roadmap_generator = MLRoadmapGenerator()


def train_roadmap_generator(user_progress_data, topic_metadata):
    """
    Train the roadmap generator with user progress data
    
    Args:
        user_progress_data: List of dicts with user progress information
        topic_metadata: Dict with topic metadata
        
    Returns:
        bool: True if training successful, False otherwise
    """
    return roadmap_generator.fit(user_progress_data, topic_metadata)


def generate_ml_roadmap(target_exam, current_level, exam_date, user_id=None):
    """
    Generate ML-based study roadmap
    
    Args:
        target_exam: Target exam or career goal
        current_level: User's current knowledge level (1-5)
        exam_date: Target exam date
        user_id: Optional user ID for personalization
        
    Returns:
        Dict with roadmap milestones
    """
    return roadmap_generator.generate_roadmap(target_exam, current_level, exam_date, user_id)


def get_topic_difficulty(topic):
    """
    Get difficulty level for a topic
    
    Args:
        topic: Topic name
        
    Returns:
        int: Difficulty level (1-5)
    """
    return roadmap_generator.get_topic_difficulty(topic)


def get_recommended_study_time(topic, user_level):
    """
    Get recommended study time for a topic
    
    Args:
        topic: Topic name
        user_level: User's current level (1-5)
        
    Returns:
        float: Recommended study time in hours
    """
    return roadmap_generator.get_recommended_study_time(topic, user_level)


def get_prerequisite_chain(topic):
    """
    Get the full prerequisite chain for a topic
    
    Args:
        topic: Topic name
        
    Returns:
        List of topics in prerequisite order
    """
    return roadmap_generator.get_prerequisite_chain(topic)


def get_learning_path_visualization(target_exam):
    """
    Get visualization data for learning path
    
    Args:
        target_exam: Target exam or career goal
        
    Returns:
        Dict with nodes and edges for visualization
    """
    return roadmap_generator.get_learning_path_visualization(target_exam)
