"""
Hugging Face API-based NLP Service for LearnNova Chatbot
Uses Hugging Face Inference API for AI responses
"""

import logging
import re
import requests
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Lazy imports for heavy dependencies
_spacy_available = False
_openai_available = False
_huggingface_available = False

# Hugging Face API configuration
HF_API_URL = (
    "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
)
HF_TOKEN = ""  # Set your Hugging Face token in environment variables

try:
    import spacy

    _spacy_available = True
except ImportError:
    logger.warning("spacy not available. Install with: pip install spacy")

try:
    import openai

    _openai_available = True
    logger.info("OpenAI package loaded successfully")
except ImportError:
    logger.warning("openai not available. Install with: pip install openai")

_huggingface_available = True
logger.info("Hugging Face API configured successfully")

# Dummy variable for compatibility (no longer used)
_transformers_available = False


class TransformerIntentClassifier:
    """
    Intent classifier using transformer models (BERT-style)
    """

    def __init__(self, model_name: str = "distilbert-base-uncased"):
        """
        Initialize the transformer-based intent classifier

        Args:
            model_name: Name of the pretrained model to use
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.intent_labels = []
        self.is_loaded = False

    def load_model(self, intent_labels: List[str] = None):
        """
        Load the transformer model and tokenizer

        Args:
            intent_labels: List of intent labels for classification
        """
        if not _transformers_available:
            logger.error("transformers library not available")
            return False

        try:
            # Default intent labels for educational chatbot
            if intent_labels is None:
                intent_labels = [
                    "greeting",
                    "goodbye",
                    "thanks",
                    "course_inquiry",
                    "recommendation",
                    "roadmap",
                    "timetable",
                    "help",
                    "pricing",
                    "enrollment",
                    "support",
                    "general",
                ]

            self.intent_labels = intent_labels

            # Load tokenizer and model
            logger.info(f"Loading transformer model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # For zero-shot classification, we'll use a different approach
            # We'll use the model's embeddings for similarity-based classification
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name, num_labels=len(intent_labels)
            )

            self.is_loaded = True
            logger.info("Transformer model loaded successfully")
            return True

        except ImportError as e:
            logger.error(
                f"Import error loading transformer model (likely protobuf incompatibility): {str(e)}"
            )
            return False
        except Exception as e:
            logger.error(f"Error loading transformer model: {str(e)}")
            return False

    def classify_intent(self, text: str, threshold: float = 0.5) -> Tuple[str, float]:
        """
        Classify the intent of input text

        Args:
            text: Input text to classify
            threshold: Confidence threshold for classification

        Returns:
            Tuple of (intent, confidence)
        """
        if not self.is_loaded or not _transformers_available:
            return self._fallback_classification(text)

        try:
            # Tokenize input
            inputs = self.tokenizer(
                text, return_tensors="pt", truncation=True, max_length=128, padding=True
            )

            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)

            # Get predicted intent
            predicted_idx = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][predicted_idx].item()

            # Apply threshold
            if confidence < threshold:
                return "general", confidence

            intent = self.intent_labels[predicted_idx]
            return intent, confidence

        except Exception as e:
            logger.error(f"Error in transformer classification: {str(e)}")
            return self._fallback_classification(text)

    def _fallback_classification(self, text: str) -> Tuple[str, float]:
        """
        Fallback keyword-based classification when transformer is unavailable
        """
        text_lower = text.lower()

        # Keyword patterns for each intent
        intent_patterns = {
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon"],
            "goodbye": ["bye", "goodbye", "see you", "take care"],
            "thanks": ["thank", "thanks", "appreciate"],
            "course_inquiry": ["course", "class", "subject", "learn", "study"],
            "recommendation": ["recommend", "suggest", "which course", "best course"],
            "roadmap": ["roadmap", "study plan", "learning path", "career path"],
            "timetable": ["timetable", "schedule", "planner", "time table"],
            "help": ["help", "assist", "support", "how to"],
            "pricing": ["price", "cost", "fee", "payment", "how much"],
            "enrollment": ["enroll", "register", "sign up", "join"],
            "support": ["problem", "issue", "error", "bug", "not working"],
        }

        for intent, patterns in intent_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return intent, 0.7

        return "general", 0.5


class SpacyEntityExtractor:
    """
    Entity extraction using spaCy NER
    """

    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize spaCy entity extractor

        Args:
            model_name: Name of spaCy model to use
        """
        self.model_name = model_name
        self.nlp = None
        self.is_loaded = False

    def load_model(self):
        """
        Load spaCy model
        """
        if not _spacy_available:
            logger.error("spacy library not available")
            return False

        try:
            logger.info(f"Loading spaCy model: {self.model_name}")
            self.nlp = spacy.load(self.model_name)
            self.is_loaded = True
            logger.info("spaCy model loaded successfully")
            return True

        except OSError:
            logger.warning(f"spaCy model {self.model_name} not found. Downloading...")
            try:
                spacy.cli.download(self.model_name)
                self.nlp = spacy.load(self.model_name)
                self.is_loaded = True
                logger.info("spaCy model downloaded and loaded successfully")
                return True
            except Exception as e:
                logger.error(f"Error downloading spaCy model: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Error loading spaCy model: {str(e)}")
            return False

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text using spaCy NER

        Args:
            text: Input text to extract entities from

        Returns:
            List of extracted entities with type and value
        """
        if not self.is_loaded or not _spacy_available:
            return self._fallback_entity_extraction(text)

        try:
            doc = self.nlp(text)
            entities = []

            for ent in doc.ents:
                entities.append(
                    {
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "description": spacy.explain(ent.label_),
                    }
                )

            # Also extract custom entities relevant to education
            custom_entities = self._extract_custom_entities(text)
            entities.extend(custom_entities)

            return entities

        except Exception as e:
            logger.error(f"Error in spaCy entity extraction: {str(e)}")
            return self._fallback_entity_extraction(text)

    def _extract_custom_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract custom entities relevant to educational context
        """
        entities = []
        text_lower = text.lower()

        # Course-related entities
        course_patterns = {
            "COURSE_NAME": [
                "web development",
                "data science",
                "machine learning",
                "cyber security",
                "cloud computing",
                "python",
                "javascript",
                "react",
                "node.js",
                "aws",
                "docker",
                "kubernetes",
            ],
            "EXAM_NAME": ["jee", "neet", "gate", "cat", "upsc", "gre", "gmat", "toefl"],
            "SUBJECT": [
                "mathematics",
                "physics",
                "chemistry",
                "biology",
                "computer science",
                "english",
                "history",
                "geography",
            ],
        }

        for entity_type, patterns in course_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    # Find the position in original text
                    start = text_lower.find(pattern)
                    entities.append(
                        {
                            "text": text[start : start + len(pattern)],
                            "label": entity_type,
                            "start": start,
                            "end": start + len(pattern),
                            "description": f"Custom entity: {entity_type}",
                        }
                    )

        return entities

    def _fallback_entity_extraction(self, text: str) -> List[Dict[str, Any]]:
        """
        Fallback regex-based entity extraction when spaCy is unavailable
        """
        entities = []

        # Simple regex patterns for common entities
        patterns = {
            "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "PHONE": r"\b\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "URL": r"https?://[^\s]+",
            "COURSE_NAME": r"\b(web development|data science|machine learning|cyber security|cloud computing)\b",
        }

        for label, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(
                    {
                        "text": match.group(),
                        "label": label,
                        "start": match.start(),
                        "end": match.end(),
                        "description": f"Regex-extracted {label}",
                    }
                )

        return entities


class EnhancedContextMemory:
    """
    Enhanced context memory system for maintaining conversation state
    """

    def __init__(self, max_history: int = 20, context_window: int = 5):
        """
        Initialize enhanced context memory

        Args:
            max_history: Maximum number of conversation turns to store
            context_window: Number of recent turns to use for context
        """
        self.max_history = max_history
        self.context_window = context_window
        self.conversation_history = defaultdict(list)
        self.user_preferences = defaultdict(dict)
        self.entity_memory = defaultdict(lambda: defaultdict(list))

    def add_conversation_turn(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        intent: str,
        entities: List[Dict[str, Any]],
        confidence: float,
    ):
        """
        Add a conversation turn to memory

        Args:
            user_id: User identifier
            user_message: User's message
            bot_response: Bot's response
            intent: Classified intent
            entities: Extracted entities
            confidence: Classification confidence
        """
        turn = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": bot_response,
            "intent": intent,
            "entities": entities,
            "confidence": confidence,
        }

        self.conversation_history[user_id].append(turn)

        # Maintain max history limit
        if len(self.conversation_history[user_id]) > self.max_history:
            self.conversation_history[user_id] = self.conversation_history[user_id][
                -self.max_history :
            ]

        # Update entity memory
        for entity in entities:
            label = entity.get("label", "UNKNOWN")
            text = entity.get("text", "")
            if text and text not in self.entity_memory[user_id][label]:
                self.entity_memory[user_id][label].append(text)

    def get_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get conversation context for a user

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing conversation context
        """
        try:
            history = self.conversation_history.get(user_id, [])
            recent_history = history[-self.context_window :] if history else []

            # Extract context from recent history
            recent_intents = [
                turn["intent"] for turn in recent_history if isinstance(turn, dict)
            ]
            recent_entities = []
            for turn in recent_history:
                if isinstance(turn, dict) and "entities" in turn:
                    ent_list = turn["entities"]
                    if isinstance(ent_list, list):
                        recent_entities.extend(ent_list)

            # Get unique entities
            unique_entities = {}
            for entity in recent_entities:
                if isinstance(entity, dict) and "label" in entity and "text" in entity:
                    key = f"{entity['label']}:{entity['text']}"
                    if key not in unique_entities:
                        unique_entities[key] = entity

            entity_mem = self.entity_memory.get(user_id, {})
            if isinstance(entity_mem, defaultdict):
                entity_mem = dict(entity_mem)

            return {
                "recent_history": recent_history,
                "recent_intents": recent_intents,
                "recent_entities": list(unique_entities.values()),
                "entity_memory": entity_mem,
                "turn_count": len(history) if isinstance(history, list) else 0,
            }
        except Exception as e:
            logger.error(f"Error getting context for user {user_id}: {e}")
            return {
                "recent_history": [],
                "recent_intents": [],
                "recent_entities": [],
                "entity_memory": {},
                "turn_count": 0,
            }

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences based on conversation history

        Args:
            user_id: User identifier

        Returns:
            Dictionary of user preferences
        """
        return self.user_preferences.get(user_id, {})

    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """
        Update user preferences

        Args:
            user_id: User identifier
            preferences: Preferences to update
        """
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}

        self.user_preferences[user_id].update(preferences)

    def clear_context(self, user_id: str):
        """
        Clear all context for a user

        Args:
            user_id: User identifier
        """
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
        if user_id in self.user_preferences:
            del self.user_preferences[user_id]
        if user_id in self.entity_memory:
            del self.entity_memory[user_id]

    def get_conversation_summary(self, user_id: str) -> str:
        """
        Generate a summary of the conversation

        Args:
            user_id: User identifier

        Returns:
            Text summary of conversation
        """
        history = self.conversation_history.get(user_id, [])

        if not history:
            return "No conversation history."

        summary_parts = []
        summary_parts.append(f"Total turns: {len(history)}")

        # Count intents
        intent_counts = defaultdict(int)
        for turn in history:
            intent_counts[turn["intent"]] += 1

        summary_parts.append("Intent distribution:")
        for intent, count in intent_counts.items():
            summary_parts.append(f"  - {intent}: {count}")

        # Mention key entities
        all_entities = []
        for turn in history:
            all_entities.extend(turn["entities"])

        if all_entities:
            entity_types = set(e["label"] for e in all_entities)
            summary_parts.append(f"Entities discussed: {', '.join(entity_types)}")

        return "\n".join(summary_parts)


class NLPService:
    """
    Main NLP service combining transformer-based intent classification,
    spaCy entity extraction, and enhanced context memory
    """

    def __init__(self, use_transformers: bool = True, use_spacy: bool = True):
        """
        Initialize NLP service

        Args:
            use_transformers: Whether to use transformer models
            use_spacy: Whether to use spaCy for NER
        """
        self.use_transformers = use_transformers
        self.use_spacy = use_spacy

        # Initialize components
        self.intent_classifier = TransformerIntentClassifier()
        self.entity_extractor = SpacyEntityExtractor()
        self.context_memory = EnhancedContextMemory()

        # Load models
        self._initialize_models()

    def _initialize_models(self):
        """
        Initialize NLP models
        """
        if self.use_transformers:
            self.intent_classifier.load_model()

        if self.use_spacy:
            self.entity_extractor.load_model()

    def process_message(
        self, user_id: str, message: str, include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user message and return comprehensive analysis
        Uses OpenAI API for real AI responses when available

        Args:
            user_id: User identifier
            message: User's message
            include_context: Whether to include conversation history

        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Try OpenAI API first for more natural responses
            if _openai_available:
                openai_response = self._get_openai_response(user_id, message)
                if openai_response:
                    # Update context memory
                    self.context_memory.add_conversation_turn(
                        user_id=user_id,
                        user_message=message,
                        bot_response=openai_response,
                        intent="openai",
                        entities=[],
                        confidence=1.0,
                    )
                    return {
                        "response": openai_response,
                        "intent": "openai",
                        "confidence": 1.0,
                        "entities": [],
                        "context": self.context_memory.get_context(user_id)
                        if include_context
                        else None,
                        "generated_by_ml": True,
                        "model_used": "openai",
                    }

            # Fall back to local NLP processing
            # Classify intent
            intent, confidence = self.intent_classifier.classify_intent(message)

            # Extract entities
            entities = self.entity_extractor.extract_entities(message)

            # Get context if requested
            context = None
            if include_context:
                context = self.context_memory.get_context(user_id)

            # Generate response based on intent and entities
            response = self._generate_response(intent, entities, context)

            # Update context memory
            self.context_memory.add_conversation_turn(
                user_id=user_id,
                user_message=message,
                bot_response=response,
                intent=intent,
                entities=entities,
                confidence=confidence,
            )

            return {
                "response": response,
                "intent": intent,
                "confidence": confidence,
                "entities": entities,
                "context": context,
                "generated_by_ml": True,
                "model_used": "transformer"
                if self.intent_classifier.is_loaded
                else "fallback",
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "response": "I'm here to help you with courses, recommendations, roadmaps, and study planning. What would you like to know?",
                "intent": "general",
                "confidence": 0.5,
                "entities": [],
                "context": None,
                "generated_by_ml": False,
                "model_used": "error_fallback",
            }

    def _get_openai_response(self, user_id: str, message: str) -> Optional[str]:
        """Get response from OpenAI API"""
        try:
            import os
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your-openai-api-key":
                return None

            client = OpenAI(api_key=api_key)

            # Get conversation history for context
            history = self.context_memory.get_context(user_id)
            messages = [{"role": "system", "content": self._get_system_prompt()}]

            if history and history.get("conversation"):
                for turn in history["conversation"][-5:]:  # Last 5 messages
                    messages.append(
                        {"role": "user", "content": turn.get("user_message", "")}
                    )
                    messages.append(
                        {"role": "assistant", "content": turn.get("bot_response", "")}
                    )

            messages.append({"role": "user", "content": message})

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.warning(f"OpenAI API call failed: {str(e)}")
            return None

    def _get_system_prompt(self) -> str:
        """Get system prompt for the AI assistant"""
        return """You are LearnNova AI Assistant, a friendly and helpful AI tutor for an online learning platform.

Your role is to help users with:
- Course information and recommendations
- Study planning and roadmaps
- Creating study timetables
- Answering questions about the platform
- Learning tips and study strategies

Be conversational, friendly, and helpful. Keep responses concise but informative.
When appropriate, suggest visiting relevant pages like /courses, /ai/recommend, /ai/roadmap-page, or /timetable.
Don't mention that you're an AI model - just be helpful as LearnNova AI Assistant."""

    def _generate_response(
        self,
        intent: str,
        entities: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a response based on intent and entities

        Args:
            intent: Classified intent
            entities: Extracted entities
            context: Conversation context

        Returns:
            Generated response text
        """
        # Intent-based response templates
        response_templates = {
            "greeting": [
                "Hello! 👋 I'm LearnNova AI Assistant. How can I help you today?",
                "Hi there! Welcome to LearnNova. What would you like to know?",
                "Hey! Great to see you. How can I assist you with your learning journey?",
            ],
            "goodbye": [
                "Goodbye! 👋 Keep learning and don't hesitate to come back if you have more questions!",
                "See you later! Best of luck with your studies!",
                "Take care! Remember, learning never stops!",
            ],
            "thanks": [
                "You're welcome! 😊 I'm glad I could help. If you have more questions, feel free to ask!",
                "My pleasure! Let me know if there's anything else I can help with.",
                "Happy to help! Don't hesitate to reach out again.",
            ],
            "course_inquiry": [
                "We offer a wide range of courses including Web Development, Data Science, Machine Learning, Cyber Security, Cloud Computing, and more! Would you like details about any specific course?",
                "Our course catalog includes both technical and non-technical subjects. What area are you interested in?",
            ],
            "recommendation": [
                "I can help you find the right courses! Visit our AI Recommendation page to get personalized course suggestions based on your goals and interests.",
                "Based on your interests, I can recommend courses that match your learning goals. Would you like me to suggest something specific?",
            ],
            "roadmap": [
                "I can create a personalized study roadmap for you! Visit our AI Roadmap page to generate a step-by-step plan for your target exam or career goal.",
                "Let me help you plan your learning path. What's your target exam or career goal?",
            ],
            "timetable": [
                "I can help you create a study schedule! Visit our Timetable page to generate a personalized weekly timetable based on your goals.",
                "Need help organizing your study time? I can create a customized timetable for you!",
            ],
            "help": [
                "I'm here to help! I can assist you with:\n• Course information and recommendations\n• Study roadmaps and planning\n• Timetable creation\n• General questions about LearnNova\n\nWhat do you need help with?",
                "How can I assist you today? I can help with courses, recommendations, roadmaps, and more!",
            ],
            "pricing": [
                "Our courses have various pricing options. Some are free, while others have premium features. Visit the Courses page to see detailed pricing for each course.",
                "Pricing varies by course. We offer both free and paid options to suit different budgets.",
            ],
            "enrollment": [
                "To enroll in a course, simply visit the Courses page, select your desired course, and click the enroll button. You'll need to create an account if you haven't already.",
                "Enrollment is easy! Browse our courses, select one you like, and follow the enrollment steps.",
            ],
            "support": [
                "I'm sorry to hear you're having an issue. Could you please describe the problem in more detail? I'll do my best to help you resolve it.",
                "Let me help you with that issue. Can you provide more details about what's not working?",
            ],
            "general": [
                "I'm here to help you with courses, recommendations, roadmaps, and study planning. What would you like to know?",
                "How can I assist you today? I can help with various aspects of your learning journey.",
            ],
        }

        # Get response for intent
        import random

        responses = response_templates.get(intent, response_templates["general"])
        response = random.choice(responses)

        # Enhance response with entity information
        if entities:
            entity_info = self._extract_entity_info(entities)
            if entity_info:
                response += f"\n\n{entity_info}"

        return response

    def _extract_entity_info(self, entities: List[Dict[str, Any]]) -> str:
        """
        Extract useful information from entities for response enhancement

        Args:
            entities: List of extracted entities

        Returns:
            Formatted entity information string
        """
        if not entities:
            return ""

        info_parts = []

        # Group entities by type
        entity_groups = defaultdict(list)
        for entity in entities:
            if isinstance(entity, dict) and "label" in entity and "text" in entity:
                entity_groups[entity["label"]].append(entity["text"])

        # Format entity information
        for entity_type, values in entity_groups.items():
            if entity_type == "COURSE_NAME":
                info_parts.append(f"I see you're interested in: {', '.join(values)}")
            elif entity_type == "EXAM_NAME":
                info_parts.append(
                    f"For {', '.join(values)} preparation, I can help you create a study plan!"
                )
            elif entity_type == "SUBJECT":
                info_parts.append(
                    f"Regarding {', '.join(values)}, we have courses and resources available!"
                )

        return " ".join(info_parts)

    def get_conversation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user

        Args:
            user_id: User identifier

        Returns:
            List of conversation turns
        """
        return self.context_memory.conversation_history.get(user_id, [])

    def clear_conversation_history(self, user_id: str):
        """
        Clear conversation history for a user

        Args:
            user_id: User identifier
        """
        self.context_memory.clear_context(user_id)

    def get_conversation_summary(self, user_id: str) -> str:
        """
        Get a summary of the conversation

        Args:
            user_id: User identifier

        Returns:
            Text summary of conversation
        """
        return self.context_memory.get_conversation_summary(user_id)


# Global NLP service instance
nlp_service = None


def get_nlp_service() -> NLPService:
    """
    Get or create the global NLP service instance

    Returns:
        NLPService instance
    """
    global nlp_service
    if nlp_service is None:
        nlp_service = NLPService(use_transformers=True, use_spacy=True)
    return nlp_service


def process_chatbot_message(user_id: str, message: str) -> Dict[str, Any]:
    """
    Process a chatbot message using the NLP service

    Args:
        user_id: User identifier
        message: User's message

    Returns:
        Dictionary containing response and metadata
    """
    service = get_nlp_service()
    return service.process_message(user_id, message)


def get_chatbot_history(user_id: str) -> List[Dict[str, Any]]:
    """
    Get chatbot conversation history

    Args:
        user_id: User identifier

    Returns:
        List of conversation turns
    """
    service = get_nlp_service()
    return service.get_conversation_history(user_id)


def clear_chatbot_history(user_id: str):
    """
    Clear chatbot conversation history

    Args:
        user_id: User identifier
    """
    service = get_nlp_service()
    service.clear_conversation_history(user_id)
