"""
ML Chatbot Engine - Intelligent Conversation System
Uses transformer-based NLP for intent classification and entity extraction
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Import the new NLP service
try:
    from services.nlp_service import (
        get_nlp_service,
        process_chatbot_message,
        get_chatbot_history,
        clear_chatbot_history
    )
    NLP_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"NLP service not available: {e}. Using fallback chatbot.")
    NLP_SERVICE_AVAILABLE = False


class MLChatbot:
    """
    ML-based Chatbot with Transformer NLP
    
    Implements intent classification, entity extraction, and context-aware
    response generation using state-of-the-art transformer models.
    """
    
    def __init__(self):
        """Initialize the ML chatbot"""
        self.nlp_service = None
        self.is_initialized = False
        
        # Initialize NLP service if available
        if NLP_SERVICE_AVAILABLE:
            try:
                self.nlp_service = get_nlp_service()
                self.is_initialized = True
                logger.info("ML Chatbot initialized with transformer-based NLP service")
            except Exception as e:
                logger.error(f"Failed to initialize NLP service: {e}")
                self.is_initialized = False
    
    def get_response(self, question: str, user_id: str = None, context: Dict = None) -> Dict[str, Any]:
        """
        Get a response to a user question using transformer-based NLP
        
        Args:
            question: User's question
            user_id: Optional user ID for context
            context: Optional conversation context
            
        Returns:
            Dict with response and metadata
        """
        try:
            # Use NLP service if available
            if self.is_initialized and self.nlp_service:
                result = self.nlp_service.process_message(
                    user_id=user_id or "anonymous",
                    message=question,
                    include_context=True
                )
                
                return {
                    'response': result['response'],
                    'intent': result['intent'],
                    'confidence': result['confidence'],
                    'entities': result.get('entities', []),
                    'context': result.get('context'),
                    'generated_by_ml': True,
                    'model_used': result.get('model_used', 'transformer')
                }
            else:
                # Fallback to simple keyword-based responses
                return self._get_fallback_response(question)
                
        except Exception as e:
            logger.error(f"Error getting chatbot response: {str(e)}")
            return self._get_fallback_response(question)
    
    def _get_fallback_response(self, question: str) -> Dict[str, Any]:
        """
        Get fallback response when NLP service is unavailable
        
        Args:
            question: User's question
            
        Returns:
            Dict with response and metadata
        """
        question_lower = question.lower()
        
        # Greeting patterns
        if any(word in question_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return {
                'response': "Hello! 👋 I'm LearnNova AI Assistant. How can I help you today?",
                'intent': 'greeting',
                'confidence': 0.9,
                'entities': [],
                'context': None,
                'generated_by_ml': False,
                'model_used': 'fallback'
            }
        
        # Thanks patterns
        if any(word in question_lower for word in ['thank', 'thanks', 'appreciate']):
            return {
                'response': "You're welcome! 😊 I'm glad I could help. If you have more questions, feel free to ask!",
                'intent': 'thanks',
                'confidence': 0.9,
                'entities': [],
                'context': None,
                'generated_by_ml': False,
                'model_used': 'fallback'
            }
        
        # Goodbye patterns
        if any(word in question_lower for word in ['bye', 'goodbye', 'see you', 'take care']):
            return {
                'response': "Goodbye! 👋 Keep learning and don't hesitate to come back if you have more questions!",
                'intent': 'goodbye',
                'confidence': 0.9,
                'entities': [],
                'context': None,
                'generated_by_ml': False,
                'model_used': 'fallback'
            }
        
        # Course inquiry patterns
        if any(word in question_lower for word in ['course', 'courses', 'class', 'subject', 'learn', 'study']):
            return {
                'response': "We offer courses in Web Development, Data Science, Machine Learning, Cyber Security, Cloud Computing, and more! Visit our Courses page to explore all options.",
                'intent': 'course_inquiry',
                'confidence': 0.8,
                'entities': [],
                'context': None,
                'generated_by_ml': False,
                'model_used': 'fallback'
            }
        
        # Recommendation patterns
        if any(word in question_lower for word in ['recommend', 'suggestion', 'which course', 'best course']):
            return {
                'response': "I can help you find the right courses! Visit our AI Recommendation page to get personalized course suggestions based on your goals and interests.",
                'intent': 'recommendation',
                'confidence': 0.8,
                'entities': [],
                'context': None,
                'generated_by_ml': False,
                'model_used': 'fallback'
            }
        
        # Roadmap patterns
        if any(word in question_lower for word in ['roadmap', 'study plan', 'learning path', 'career path']):
            return {
                'response': "I can create a personalized study roadmap for you! Visit our AI Roadmap page to generate a step-by-step plan for your target exam.",
                'intent': 'roadmap',
                'confidence': 0.8,
                'entities': [],
                'context': None,
                'generated_by_ml': False,
                'model_used': 'fallback'
            }
        
        # Timetable patterns
        if any(word in question_lower for word in ['timetable', 'schedule', 'planner', 'time table']):
            return {
                'response': "I can help you create a study schedule! Visit our Timetable page to generate a personalized weekly timetable based on your goals.",
                'intent': 'timetable',
                'confidence': 0.8,
                'entities': [],
                'context': None,
                'generated_by_ml': False,
                'model_used': 'fallback'
            }
        
        # Help patterns
        if any(word in question_lower for word in ['help', 'assist', 'support', 'how to']):
            return {
                'response': "I'm here to help! I can assist you with:\n• Course information and recommendations\n• Study roadmaps and planning\n• Timetable creation\n• General questions about LearnNova\n\nWhat do you need help with?",
                'intent': 'help',
                'confidence': 0.8,
                'entities': [],
                'context': None,
                'generated_by_ml': False,
                'model_used': 'fallback'
            }
        
        # Pricing patterns
        if any(word in question_lower for word in ['price', 'cost', 'fee', 'payment', 'how much']):
            return {
                'response': "Our courses have various pricing options. Some are free, while others have premium features. Visit the Courses page to see detailed pricing for each course.",
                'intent': 'pricing',
                'confidence': 0.8,
                'entities': [],
                'context': None,
                'generated_by_ml': False,
                'model_used': 'fallback'
            }
        
        # Enrollment patterns
        if any(word in question_lower for word in ['enroll', 'register', 'sign up', 'join']):
            return {
                'response': "To enroll in a course, simply visit the Courses page, select your desired course, and click the enroll button. You'll need to create an account if you haven't already.",
                'intent': 'enrollment',
                'confidence': 0.8,
                'entities': [],
                'context': None,
                'generated_by_ml': False,
                'model_used': 'fallback'
            }
        
        # Support patterns
        if any(word in question_lower for word in ['problem', 'issue', 'error', 'bug', 'not working']):
            return {
                'response': "I'm sorry to hear you're having an issue. Could you please describe the problem in more detail? I'll do my best to help you resolve it.",
                'intent': 'support',
                'confidence': 0.8,
                'entities': [],
                'context': None,
                'generated_by_ml': False,
                'model_used': 'fallback'
            }
        
        # Default fallback
        return {
            'response': "I'm here to help you with courses, recommendations, roadmaps, and study planning. What would you like to know?",
            'intent': 'general',
            'confidence': 0.5,
            'entities': [],
            'context': None,
            'generated_by_ml': False,
            'model_used': 'fallback'
        }
    
    def get_conversation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of conversation entries
        """
        if self.is_initialized and self.nlp_service:
            try:
                return self.nlp_service.get_conversation_history(user_id)
            except Exception as e:
                logger.error(f"Error getting conversation history: {e}")
                return []
        return []
    
    def clear_conversation_history(self, user_id: str):
        """
        Clear conversation history for a user
        
        Args:
            user_id: User ID
        """
        if self.is_initialized and self.nlp_service:
            try:
                self.nlp_service.clear_conversation_history(user_id)
            except Exception as e:
                logger.error(f"Error clearing conversation history: {e}")
    
    def get_conversation_summary(self, user_id: str) -> str:
        """
        Get a summary of the conversation
        
        Args:
            user_id: User ID
            
        Returns:
            Text summary of conversation
        """
        if self.is_initialized and self.nlp_service:
            try:
                return self.nlp_service.get_conversation_summary(user_id)
            except Exception as e:
                logger.error(f"Error getting conversation summary: {e}")
                return "Unable to generate summary."
        return "NLP service not available."


# Global instance
chatbot = MLChatbot()


def train_chatbot(training_data: List[Dict[str, str]]) -> bool:
    """
    Train the chatbot with training data
    
    Note: With transformer-based models, training is typically done offline.
    This function is kept for backward compatibility but may not be used.
    
    Args:
        training_data: List of dicts with 'question', 'intent', 'response'
        
    Returns:
        bool: True if training successful, False otherwise
    """
    logger.info("Training not required for transformer-based chatbot. Models are pre-trained.")
    return True


def get_chatbot_response(question: str, user_id: str = None, context: Dict = None) -> Dict[str, Any]:
    """
    Get a response from the chatbot
    
    Args:
        question: User's question
        user_id: Optional user ID for context
        context: Optional conversation context
        
    Returns:
        Dict with response and metadata
    """
    return chatbot.get_response(question, user_id, context)


def get_conversation_history(user_id: str) -> List[Dict[str, Any]]:
    """
    Get conversation history for a user
    
    Args:
        user_id: User ID
        
    Returns:
        List of conversation entries
    """
    return chatbot.get_conversation_history(user_id)


def clear_conversation_history(user_id: str):
    """
    Clear conversation history for a user
    
    Args:
        user_id: User ID
    """
    chatbot.clear_conversation_history(user_id)


def get_conversation_summary(user_id: str) -> str:
    """
    Get a summary of the conversation
    
    Args:
        user_id: User ID
        
    Returns:
        Text summary of conversation
    """
    return chatbot.get_conversation_summary(user_id)
