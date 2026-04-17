# LearnNova

An AI-Powered E-Learning Platform built with Flask and Machine Learning.

## Author

Gaurav

## Deploy to Render (Free)

1. **Push to GitHub** - Upload this project to a GitHub repository

2. **Create Render Account** - Go to [render.com](https://render.com) and sign up

3. **Deploy**:
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - Name: `learnnova`
     - Build Command: (leave blank)
     - Start Command: `python app.py`
   - Click "Create Web Service"

4. **Done** - Your app will be live at `https://learnnova.onrender.com`

## Description

LearnNova is a comprehensive e-learning platform that provides online courses, tests, timetables, and AI-powered learning features. It features a modern design with dark mode support, responsive layouts, and an intuitive user interface.

The platform includes advanced ML/AI features for personalized learning:
- **ML Chatbot** - Transformer-based NLP for intelligent conversations
- **ML Recommendation Engine** - Hybrid filtering (SVD + Content-based + Collaborative)
- **ML Roadmap Generator** - DAG-based topic sequencing with prerequisite mapping
- **ML Study Planner** - Constraint-based scheduling with greedy optimization

## 🌐 Site Flow & Architecture

### How the Site Works:

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER VISITS SITE                         │
│                          (http://127.0.0.1:5000/)               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Flask App (app.py)                         │
│  • Registers all blueprints (routes, models, templates)         │
│  • Handles database initialization                              │
│  • Manages user sessions & authentication                       │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   ROUTES      │      │    MODELS     │      │  TEMPLATES    │
│   (routes/)   │      │   (models/)   │      │ (templates/)  │
└───────────────┘      └───────────────┘      └───────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
  • / (home)              • User              • index.html
  • /courses             • Course             • dashboard.html
  • /dashboard            • Enrollment         • courses.html
  • /timetable           • Test                • ai_roadmap.html
  • /ai/roadmap-page     • Timetable           • timetable.html
  • /tests               • Roadmap             • etc.
  • /ai/chat             • TestResult           • ai_recommendation.html
```

### User Journey:

```
VISITOR → REGISTER → LOGIN → BROWSE COURSES → ENROLL → STUDY
                                      │
                                      ▼
                             ACCESS AI FEATURES
                                      │
               ┌──────────────────────┼──────────────────────┐
               │                      │                      │
               ▼                      ▼                      ▼
      ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
      │AI Roadmap  │         │AI Timetable │        │AI Recommend │
      │(What to    │         │(When to     │        │(Which       │
      │ achieve)   │         │ study)      │        │ courses)    │
      └─────────────┘        └─────────────┘        └─────────────┘
                              │
                              ▼
                     ┌─────────────┐
                     │ML Chatbot   │
                     │(Ask any     │
                     │ question)   │
                     └─────────────┘
```

### Key Pages & Features:

| Route | File | Description |
|-------|------|-------------|
| `/` | `templates/index.html` | Home page with course carousel |
| `/courses` | `routes/courses.py` | Browse all courses |
| `/dashboard` | `routes/dashboard.py` | Student dashboard |
| `/timetable` | `routes/timetable.py` | AI Study Planner (schedule) |
| `/ai/roadmap-page` | `routes/ai.py` | AI Study Roadmap (milestones) |
| `/ai/recommend` | `routes/ai.py` | AI Course Recommendations |
| `/ai/chat` | `routes/ai.py` | ML Chatbot |
| `/tests` | `routes/tests.py` | Mock test series |
| `/become-teacher` | `routes/teacher.py` | Apply to teach |

### Database Models:

- **User** - Students, Teachers, Admins
- **Course** - Title, description, content, teacher
- **Enrollment** - Links students to courses with progress
- **Test** - Quizzes with questions
- **TestResult** - Student test attempts
- **TimetableItem** - AI-generated study schedule
- **Roadmap** - Saved roadmaps

### AI/ML Features:

The platform includes four major ML-powered components:

1. **ML Chatbot** (`routes/ml_chatbot.py`)
   - Transformer-based NLP for intent classification
   - Entity extraction and context-aware responses
   - Fallback keyword-based responses when NLP unavailable

2. **ML Recommendation Engine** (`routes/ml_recommendation.py`)
   - SVD Matrix Factorization for latent factor discovery
   - User embeddings for deep personalization
   - Hybrid filtering (Content-based + Collaborative)
   - Multiple strategies: user_based, item_based, hybrid

3. **ML Roadmap Generator** (`routes/ml_roadmap.py`)
   - DAG-based topic sequencing with prerequisite mapping
   - Difficulty estimation based on user performance
   - Supports multiple exam types: UPSC, Web Dev, Data Science, ML, Cyber Security, Cloud Computing, Placement Prep

4. **ML Study Planner** (`routes/ml_study_planner.py`)
   - Constraint-based scheduling with greedy optimization
   - Considers time slots, deadlines, difficulty weights
   - Spaced repetition and weekend mock tests
   - Personalized time allocation based on user preferences

### Tech Stack:

- **Backend**: Flask (Python)
- **Database**: SQLite (instance/learnnova.db)
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Bootstrap 5
- **Authentication**: Flask-Login
- **ML Libraries**: NumPy, Pandas, Scikit-Learn
- **API**: RESTful API in `api/v1/`

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# Open in browser
http://127.0.0.1:5000
```

## Project Structure

```
learnnova/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── routes/             # URL handlers
│   ├── ai.py          # AI features & endpoints
│   ├── ml_chatbot.py  # ML Chatbot Engine
│   ├── ml_recommendation.py  # ML Recommendation Engine
│   ├── ml_roadmap.py  # ML Roadmap Generator
│   ├── ml_study_planner.py   # ML Study Planner
│   ├── auth.py        # Authentication
│   ├── courses.py     # Course management
│   ├── dashboard.py   # Student dashboard
│   ├── timetable.py   # Study planner
│   └── teacher.py     # Teacher features
├── models/            # Database models
├── services/          # Business logic services
│   ├── nlp_service.py # NLP service
│   ├── recommendation_service.py
│   └── cache_service.py
├── templates/         # HTML pages
├── css/, js/, img/   # Static files
├── lib/              # Third-party libraries
└── instance/         # SQLite database
```

## License

MIT License
