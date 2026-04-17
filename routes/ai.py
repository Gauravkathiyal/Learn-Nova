"""
AI Routes - AI-powered features
"""

import os
import re
from flask import Blueprint, render_template, request, jsonify  # type: ignore[import]
from flask_login import login_required, current_user  # type: ignore[import]
from routes.ml_recommendation import (
    train_recommender,
    get_ml_recommendations,
    get_popular_courses,
    get_similar_courses,
)
from routes.ml_roadmap import (
    generate_ml_roadmap,
    get_topic_difficulty,
    get_recommended_study_time,
)
from routes.ml_study_planner import generate_ml_timetable, get_optimal_study_time
from routes.ml_chatbot import (
    get_chatbot_response,
    get_conversation_history,
    clear_conversation_history,
)

ai = Blueprint("ai", __name__)


@ai.route("/ai/ask", methods=["POST"])
def ask_question():
    """Ask AI a question about any topic - ML-powered only"""
    data = request.get_json()
    question = data.get("question", "")

    if not question:
        return jsonify({"success": False, "error": "Question is required"}), 400

    # Use authenticated user ID or "anonymous" for unauthenticated users
    user_id = str(current_user.id) if current_user.is_authenticated else "anonymous"

    # Get ML chatbot response
    ml_response = get_chatbot_response(question, user_id)

    if ml_response:
        answer = ml_response.get("response", "I'm here to help! Please try again.")
        ml_generated = ml_response.get("generated_by_ml", True)
    else:
        answer = "I'm here to help! Please try again."
        ml_generated = False

    response = {"success": True, "response": answer, "ml_generated": ml_generated}

    return jsonify(response)


@ai.route("/ai/recommend")
@login_required
def recommend_courses():
    """AI-powered course recommendations - shows questionnaire"""
    return render_template("ai_recommendation.html")


@ai.route("/ai/ml-recommendations/train", methods=["POST"])
@login_required
def train_ml_recommender():
    """Train the ML recommender system with enrollment data"""
    from models.course import Enrollment

    try:
        # Get all enrollments with progress data
        enrollments = Enrollment.query.filter(
            Enrollment.status.in_(["active", "completed"])
        ).all()

        # Prepare data for training
        enrollments_data = [
            {
                "user_id": e.user_id,
                "course_id": e.course_id,
                "progress_percent": e.progress_percent or 0,
            }
            for e in enrollments
        ]

        # Train the recommender
        success = train_recommender(enrollments_data)

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": f"ML recommender trained with {len(enrollments_data)} enrollments",
                    "enrollments_count": len(enrollments_data),
                }
            )
        else:
            return jsonify(
                {"success": False, "error": "Failed to train ML recommender"}
            ), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ai.route("/ai/ml-recommendations/get", methods=["POST"])
@login_required
def get_ml_course_recommendations():
    """Get ML-based course recommendations for current user"""
    from models.course import Course

    try:
        data = request.get_json() or {}
        method = data.get("method", "hybrid")  # user_based, item_based, hybrid
        n_recommendations = data.get("n_recommendations", 6)

        # Get ML recommendations
        ml_recs = get_ml_recommendations(
            user_id=current_user.id, n_recommendations=n_recommendations, method=method
        )

        # If no ML recommendations, fall back to popular courses
        if not ml_recs:
            popular = get_popular_courses(n_recommendations)
            ml_recs = [
                {"course_id": p["course_id"], "score": p["popularity_score"]}
                for p in popular
            ]

        # Get course details
        recommended_courses = []
        for rec in ml_recs:
            course = Course.query.get(rec["course_id"])
            if course and course.is_published:
                recommended_courses.append(
                    {
                        "course": course.to_dict(),
                        "score": rec["score"],
                        "reason": f"Based on similar learners"
                        if method == "user_based"
                        else f"Similar to courses you like"
                        if method == "item_based"
                        else f"Personalized recommendation",
                    }
                )

        # Generate HTML
        recommendations_html = ""
        if recommended_courses:
            recommendations_html = '<div class="row">'
            for item in recommended_courses:
                course = item["course"]
                price_display = "Free" if course["is_free"] else f"₹{course['price']}"
                level_display = (
                    course["level"].capitalize() if course["level"] else "All Levels"
                )

                recommendations_html += f'''
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card h-100 shadow-sm border-0">
                        <img src="{course["thumbnail"] or "/img/course-1.jpg"}" class="card-img-top" alt="{course["title"]}" style="height: 180px; object-fit: cover;">
                        <div class="card-body">
                            <div class="d-flex justify-content-between mb-2">
                                <span class="badge bg-primary">{course["category"]}</span>
                                <span class="text-muted">{level_display}</span>
                            </div>
                            <h5 class="card-title">{course["title"]}</h5>
                            <p class="card-text text-muted small">{course["description"][:100] if course["description"] else ""}...</p>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="h5 mb-0 text-primary">{price_display}</span>
                                <a href="/course/{course["id"]}" class="btn btn-sm btn-outline-primary">View Course</a>
                            </div>
                        </div>
                    </div>
                </div>
                '''
            recommendations_html += "</div>"

            # Add explanation
            recommendations_html += f"""
            <div class="alert alert-info mt-4">
                <h5><i class="fas fa-robot me-2"></i>AI-Powered Recommendations</h5>
                <p>These recommendations are generated using <strong>collaborative filtering</strong> - 
                an ML algorithm that analyzes enrollment patterns of similar learners to suggest courses 
                you're likely to enjoy. Method: <code>{method}</code></p>
            </div>
            """
        else:
            recommendations_html = """
            <div class="alert alert-warning">
                <h5>No recommendations available</h5>
                <p>We need more enrollment data to generate personalized recommendations. 
                Enroll in some courses and we'll provide better suggestions!</p>
                <a href="/courses" class="btn btn-primary">Browse All Courses</a>
            </div>
            """

        return jsonify(
            {
                "success": True,
                "recommendations_html": recommendations_html,
                "method": method,
                "count": len(recommended_courses),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ai.route("/ai/ml-recommendations/similar/<int:course_id>")
@login_required
def get_similar_courses_endpoint(course_id):
    """Get courses similar to a given course"""
    from models.course import Course

    try:
        n_similar = request.args.get("n", 5, type=int)

        # Get similar courses
        similar = get_similar_courses(course_id, n_similar)

        # Get course details
        similar_courses = []
        for item in similar:
            course = Course.query.get(item["course_id"])
            if course and course.is_published:
                similar_courses.append(
                    {
                        "course": course.to_dict(),
                        "similarity_score": item["similarity_score"],
                    }
                )

        return jsonify(
            {
                "success": True,
                "similar_courses": similar_courses,
                "count": len(similar_courses),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ai.route("/ai/roadmap-page")
@login_required
def roadmap_page():
    """AI Study Roadmap - shows questionnaire page"""
    return render_template("ai_roadmap.html")


@ai.route("/ai/recommend/submit", methods=["POST"])
@login_required
def submit_recommendation_answers():
    """Process questionnaire answers and generate AI-filtered course recommendations"""
    import logging

    logger = logging.getLogger(__name__)

    data = request.get_json()

    from models.course import Course, Enrollment
    from sqlalchemy import or_

    # Get primary goals
    goals = data.get("goals", [])

    # Map goals to specific course categories
    goal_category_mapping = {
        "tech": [
            "Programming & Development",
            "Data Science & AI",
            "Cyber Security",
            "UI / UX Design",
        ],
        "govt": ["Competitive Exams", "UPSC", "SSC", "Banking"],
        "business": ["Business", "Digital Marketing", "Entrepreneurship"],
        "engg": ["Engineering", "JEE Preparation", "Competitive Exams"],
    }

    # Map tech interests (Q2) to specific categories/keywords
    tech_interests = data.get("q2", [])
    if isinstance(tech_interests, str):
        tech_interests = [tech_interests]

    tech_interest_mapping = {
        "web_dev": ["Web Development", "Full Stack", "Frontend", "React"],
        "data_science": ["Data Science", "Data Analytics", "Machine Learning", "AI"],
        "mobile_dev": ["Mobile Development", "Flutter", "Android", "iOS"],
        "cloud_devops": ["Cloud Computing", "AWS", "DevOps"],
        "cyber_security": ["Cyber Security", "Ethical Hacking"],
        "ui_ux": ["UI / UX Design", "UI/UX", "Design"],
        "blockchain": ["Blockchain", "Web3"],
        "game_dev": ["Game Development", "Unity"],
    }

    # Map programming languages (Q8) to keywords
    languages = data.get("q8", [])
    if isinstance(languages, str):
        languages = [languages]

    lang_mapping = {
        "python": ["Python"],
        "javascript": ["JavaScript", "React", "Node.js"],
        "java": ["Java"],
        "cpp": ["C++", "Data Structures"],
        "go": ["Go", "Golang"],
        "swift": ["Swift", "iOS"],
        "kotlin": ["Kotlin", "Android"],
        "dart": ["Dart", "Flutter"],
    }

    # Build category filters from goals
    category_filters = set()
    for goal in goals:
        if goal in goal_category_mapping:
            category_filters.update(goal_category_mapping[goal])

    # Build specific keyword filters from tech interests and languages
    keyword_filters = set()
    for interest in tech_interests:
        if interest in tech_interest_mapping:
            keyword_filters.update(tech_interest_mapping[interest])
    for lang in languages:
        if lang in lang_mapping:
            keyword_filters.update(lang_mapping[lang])

    # Map govt exams (Q3) to keywords
    govt_exams = data.get("q3", [])
    if isinstance(govt_exams, str):
        govt_exams = [govt_exams]
    govt_mapping = {
        "upsc": ["UPSC", "Civil Services"],
        "ssc": ["SSC", "CGL"],
        "railway": ["Railway"],
        "banking": ["Banking", "IBPS", "SBI"],
        "state_psc": ["State PSC"],
        "defence": ["NDA", "CDS", "Defence"],
    }
    for exam in govt_exams:
        if exam in govt_mapping:
            keyword_filters.update(govt_mapping[exam])

    # Get experience level (Q5) for filtering
    experience_level = data.get("q5", [""])[0] if data.get("q5") else ""
    level_filter = None
    if experience_level == "beginner":
        level_filter = "beginner"
    elif experience_level == "some_knowledge":
        level_filter = "beginner"
    elif experience_level == "intermediate":
        level_filter = "intermediate"
    elif experience_level == "advanced":
        level_filter = "advanced"

    # Get budget (Q7) for filtering
    budget = data.get("q7", [""])[0] if data.get("q7") else ""

    def apply_budget_filter(query):
        """Apply budget filter to a query"""
        if budget == "free":
            return query.filter(Course.is_free == True)
        elif budget == "low":
            return query.filter(or_(Course.is_free == True, Course.price <= 1000))
        elif budget == "medium":
            return query.filter(or_(Course.is_free == True, Course.price <= 5000))
        elif budget == "high":
            return query.filter(or_(Course.is_free == True, Course.price <= 15000))
        return query

    def apply_level_filter(query):
        """Apply experience level filter to a query"""
        if level_filter:
            return query.filter(Course.level == level_filter)
        return query

    matching_courses = []

    # Strategy 1: Filter by category + keywords + level + budget
    if category_filters:
        cat_conditions = [Course.category.ilike(f"%{cat}%") for cat in category_filters]
        base_query = Course.query.filter(
            Course.is_published == True, or_(*cat_conditions)
        )

        # Add keyword filter if available (narrow within category)
        if keyword_filters:
            kw_conditions = []
            for term in keyword_filters:
                kw_conditions.append(Course.title.ilike(f"%{term}%"))
                kw_conditions.append(Course.description.ilike(f"%{term}%"))
            base_query = base_query.filter(or_(*kw_conditions))

        base_query = apply_level_filter(base_query)
        base_query = apply_budget_filter(base_query)
        matching_courses = (
            base_query.order_by(Course.rating.desc(), Course.total_students.desc())
            .limit(12)
            .all()
        )

    # Strategy 2: If no category match, filter by keywords only
    if not matching_courses and keyword_filters:
        kw_conditions = []
        for term in keyword_filters:
            kw_conditions.append(Course.title.ilike(f"%{term}%"))
            kw_conditions.append(Course.category.ilike(f"%{term}%"))

        base_query = Course.query.filter(
            Course.is_published == True, or_(*kw_conditions)
        )
        base_query = apply_level_filter(base_query)
        base_query = apply_budget_filter(base_query)
        matching_courses = (
            base_query.order_by(Course.rating.desc(), Course.total_students.desc())
            .limit(12)
            .all()
        )

    # Strategy 3: If still no matches, relax level filter but keep category
    if not matching_courses and category_filters:
        cat_conditions = [Course.category.ilike(f"%{cat}%") for cat in category_filters]
        base_query = Course.query.filter(
            Course.is_published == True, or_(*cat_conditions)
        )
        base_query = apply_budget_filter(base_query)
        matching_courses = (
            base_query.order_by(Course.rating.desc(), Course.total_students.desc())
            .limit(12)
            .all()
        )

    # Strategy 4: Last resort - get popular courses matching budget only
    if not matching_courses:
        base_query = Course.query.filter(Course.is_published == True)
        base_query = apply_budget_filter(base_query)
        matching_courses = (
            base_query.order_by(Course.rating.desc(), Course.total_students.desc())
            .limit(6)
            .all()
        )

    # Now apply ML scoring to rank the filtered courses
    ml_recommendations = []
    ml_used = False

    try:
        enrollments = Enrollment.query.filter(
            Enrollment.status.in_(["active", "completed"])
        ).all()

        if enrollments:
            enrollments_data = [
                {
                    "user_id": e.user_id,
                    "course_id": e.course_id,
                    "progress_percent": e.progress_percent or 0,
                }
                for e in enrollments
            ]

            train_recommender(enrollments_data)

            ml_recs = get_ml_recommendations(
                user_id=current_user.id, n_recommendations=24, method="hybrid"
            )

            ml_score_map = {rec["course_id"]: rec["score"] for rec in ml_recs}

            scored_courses = []
            for course in matching_courses:
                ml_score = ml_score_map.get(course.id, 0)
                scored_courses.append(
                    {
                        "course": course,
                        "score": ml_score,
                        "reason": "Based on your interests and similar learners"
                        if ml_score > 0
                        else "Based on your questionnaire answers",
                    }
                )

            scored_courses.sort(key=lambda x: x["score"], reverse=True)
            ml_recommendations = scored_courses[:12]

            if any(rec["score"] > 0 for rec in ml_recommendations):
                ml_used = True
    except Exception as e:
        logger.error(f"Error getting ML recommendations: {str(e)}")

    # Prepare final recommendations
    if ml_recommendations:
        recommended_courses = ml_recommendations
    else:
        recommended_courses = [
            {
                "course": course,
                "score": 0,
                "reason": "Based on your questionnaire answers",
            }
            for course in matching_courses[:12]
        ]

    # Generate recommendations HTML
    recommendations_html = ""

    if recommended_courses:
        if ml_used:
            recommendations_html = '<div class="text-center mb-4"><span class="ml-badge"><i class="fas fa-robot me-2"></i>AI-Powered Recommendations</span></div>'

        recommendations_html += '<div class="row">'
        for idx, item in enumerate(recommended_courses):
            course = item["course"]
            price_display = "Free" if course.is_free else f"₹{course.price}"
            level_display = course.level.capitalize() if course.level else "All Levels"

            score_html = ""
            if ml_used and item["score"] > 0:
                score = item["score"]
                score_html = f'<div class="mt-2"><span class="score-badge"><i class="fas fa-chart-line me-1"></i>Match: {score:.1%}</span></div>'

            recommendations_html += f'''
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100 shadow-sm border-0 recommendation-card">
                    <div style="overflow: hidden;">
                        <img src="{course.thumbnail or "/img/course-1.jpg"}" class="card-img-top" alt="{course.title}" style="height: 180px; object-fit: cover;">
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span class="badge bg-primary">{course.category}</span>
                            <span class="text-muted">{level_display}</span>
                        </div>
                        <h5 class="card-title">{course.title}</h5>
                        <p class="card-text text-muted small">{course.description[:100] if course.description else ""}...</p>
                        {score_html}
                        <div class="d-flex justify-content-between align-items-center mt-3">
                            <span class="h5 mb-0 text-primary">{price_display}</span>
                            <a href="/course/{course.id}" class="btn btn-sm btn-outline-primary">View Course</a>
                        </div>
                    </div>
                </div>
            </div>
            '''
        recommendations_html += "</div>"

        goals_text = (
            ", ".join([g.capitalize() for g in goals[:2]]) if goals else "your goals"
        )

        if ml_used:
            recommendations_html += f"""
            <div class="alert alert-info mt-4">
                <h5><i class="fas fa-robot me-2"></i>AI-Powered Recommendations</h5>
                <p>These recommendations are generated using <strong>machine learning</strong> - our algorithm analyzes your questionnaire answers and enrollment patterns of similar learners to suggest courses you're likely to enjoy. Based on your interest in <strong>{goals_text}</strong>, we've personalized these suggestions just for you.</p>
            </div>
            """
        else:
            recommendations_html += f"""
            <div class="alert alert-info mt-4">
                <h5><i class="fas fa-lightbulb me-2"></i>Why these courses?</h5>
                <p>Based on your interest in <strong>{goals_text}</strong>, we have selected courses that match your learning objectives. These courses will help you build the skills you need to achieve your career goals.</p>
            </div>
            """
    else:
        recommendations_html = """
        <div class="alert alert-warning">
            <h5>No specific courses found</h5>
            <p>We couldn't find courses matching your specific criteria. Please browse our complete course catalog.</p>
            <a href="/courses" class="btn btn-primary">Browse All Courses</a>
        </div>
        """

    # Apply budget filter
    if budget == "medium":
        base_query = base_query.filter(
            or_(Course.is_free == True, Course.price <= 5000)
        )
    elif budget == "high":
        base_query = base_query.filter(
            or_(Course.is_free == True, Course.price <= 15000)
        )

    # Get matching courses
    matching_courses = base_query.order_by(Course.total_students.desc()).limit(24).all()

    # If no courses found with filters, try without level filter
    if not matching_courses and level_filter:
        base_query_no_level = Course.query.filter(Course.is_published == True)
        if search_terms:
            search_conditions = []
            for term in search_terms:
                search_conditions.append(Course.title.ilike(f"%{term}%"))
                search_conditions.append(Course.description.ilike(f"%{term}%"))
                search_conditions.append(Course.category.ilike(f"%{term}%"))
            base_query_no_level = base_query_no_level.filter(or_(*search_conditions))

        # Apply budget filter
        if budget == "free":
            base_query_no_level = base_query_no_level.filter(Course.is_free == True)
        elif budget == "low":
            base_query_no_level = base_query_no_level.filter(
                or_(Course.is_free == True, Course.price <= 1000)
            )
        elif budget == "medium":
            base_query_no_level = base_query_no_level.filter(
                or_(Course.is_free == True, Course.price <= 5000)
            )
        elif budget == "high":
            base_query_no_level = base_query_no_level.filter(
                or_(Course.is_free == True, Course.price <= 15000)
            )

        matching_courses = (
            base_query_no_level.order_by(Course.total_students.desc()).limit(24).all()
        )

    # If still no courses, get popular courses
    if not matching_courses:
        matching_courses = (
            Course.query.filter(Course.is_published == True)
            .order_by(Course.total_students.desc())
            .limit(12)
            .all()
        )

    # Now try to apply ML scoring to rank the filtered courses
    ml_recommendations = []
    ml_used = False

    try:
        # Train recommender if not already trained
        enrollments = Enrollment.query.filter(
            Enrollment.status.in_(["active", "completed"])
        ).all()

        if enrollments:
            enrollments_data = [
                {
                    "user_id": e.user_id,
                    "course_id": e.course_id,
                    "progress_percent": e.progress_percent or 0,
                }
                for e in enrollments
            ]

            # Train the recommender
            train_recommender(enrollments_data)

            # Get ML recommendations for current user
            ml_recs = get_ml_recommendations(
                user_id=current_user.id, n_recommendations=24, method="hybrid"
            )

            # Create a mapping of course_id to ML score
            ml_score_map = {rec["course_id"]: rec["score"] for rec in ml_recs}

            # Score the matching courses using ML scores
            scored_courses = []
            for course in matching_courses:
                ml_score = ml_score_map.get(course.id, 0)
                scored_courses.append(
                    {
                        "course": course,
                        "score": ml_score,
                        "reason": "Based on your interests and similar learners"
                        if ml_score > 0
                        else "Based on your questionnaire answers",
                    }
                )

            # Sort by ML score (higher is better)
            scored_courses.sort(key=lambda x: x["score"], reverse=True)

            # Take top 12
            ml_recommendations = scored_courses[:12]

            if any(rec["score"] > 0 for rec in ml_recommendations):
                ml_used = True
    except Exception as e:
        logger.error(f"Error getting ML recommendations: {str(e)}")

    # Prepare final recommendations
    recommended_courses = []

    if ml_recommendations:
        # Use ML-scored recommendations
        recommended_courses = ml_recommendations
    else:
        # Use keyword-filtered courses without ML scoring
        recommended_courses = [
            {
                "course": course,
                "score": 0,
                "reason": "Based on your questionnaire answers",
            }
            for course in matching_courses[:12]
        ]

    # Generate recommendations HTML
    recommendations_html = ""

    if recommended_courses:
        # Add ML badge if ML recommendations were used
        if ml_used:
            recommendations_html = '<div class="text-center mb-4"><span class="ml-badge"><i class="fas fa-robot me-2"></i>AI-Powered Recommendations</span></div>'

        recommendations_html += '<div class="row">'
        for idx, item in enumerate(recommended_courses):
            course = item["course"]
            price_display = "Free" if course.is_free else f"₹{course.price}"
            level_display = course.level.capitalize() if course.level else "All Levels"

            # Get score if available from ML recommendations
            score_html = ""
            if ml_used and item["score"] > 0:
                score = item["score"]
                score_html = f'<div class="mt-2"><span class="score-badge"><i class="fas fa-chart-line me-1"></i>Match: {score:.1%}</span></div>'

            recommendations_html += f'''
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100 shadow-sm border-0 recommendation-card">
                    <div style="overflow: hidden;">
                        <img src="{course.thumbnail or "/img/course-1.jpg"}" class="card-img-top" alt="{course.title}" style="height: 180px; object-fit: cover;">
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span class="badge bg-primary">{course.category}</span>
                            <span class="text-muted">{level_display}</span>
                        </div>
                        <h5 class="card-title">{course.title}</h5>
                        <p class="card-text text-muted small">{course.description[:100] if course.description else ""}...</p>
                        {score_html}
                        <div class="d-flex justify-content-between align-items-center mt-3">
                            <span class="h5 mb-0 text-primary">{price_display}</span>
                            <a href="/course/{course.id}" class="btn btn-sm btn-outline-primary">View Course</a>
                        </div>
                    </div>
                </div>
            </div>
            '''
        recommendations_html += "</div>"

        # Add explanation based on whether ML was used
        goals_text = (
            ", ".join([g.capitalize() for g in goals[:2]]) if goals else "your goals"
        )

        if ml_used:
            recommendations_html += f"""
            <div class="alert alert-info mt-4">
                <h5><i class="fas fa-robot me-2"></i>AI-Powered Recommendations</h5>
                <p>These recommendations are generated using <strong>machine learning</strong> - our algorithm analyzes your questionnaire answers and enrollment patterns of similar learners to suggest courses you're likely to enjoy. Based on your interest in <strong>{goals_text}</strong>, we've personalized these suggestions just for you.</p>
            </div>
            """
        else:
            recommendations_html += f"""
            <div class="alert alert-info mt-4">
                <h5><i class="fas fa-lightbulb me-2"></i>Why these courses?</h5>
                <p>Based on your interest in <strong>{goals_text}</strong>, we have selected courses that match your learning objectives. These courses will help you build the skills you need to achieve your career goals.</p>
            </div>
            """
    else:
        recommendations_html = """
        <div class="alert alert-warning">
            <h5>No specific courses found</h5>
            <p>We couldn't find courses matching your specific criteria. Please browse our complete course catalog.</p>
            <a href="/courses" class="btn btn-primary">Browse All Courses</a>
        </div>
        """

    return jsonify(
        {
            "success": True,
            "recommendations_html": recommendations_html,
            "ml_used": ml_used,
        }
    )


@ai.route("/ai/roadmap/generate", methods=["POST"])
@login_required
def generate_roadmap():
    """Generate AI study roadmap using ML module"""
    data = request.get_json()
    roadmap_type = data.get("roadmap_type", "study")
    target_exam = data.get("target_exam", "")
    project_type = data.get("project_type", "")
    career_goal = data.get("career_goal", "")
    current_level = data.get("current_level", "beginner")
    timeline = data.get("timeline", "6months")
    study_hours = data.get("study_hours", "4")

    # Timeline mapping
    timeline_map = {
        "1month": "1 month",
        "3months": "3 months",
        "6months": "6 months",
        "1year": "1 year",
    }
    timeline_display = timeline_map.get(timeline, "6 months")

    # Level mapping
    level_map = {
        "beginner": "Beginner",
        "some_knowledge": "Some Knowledge",
        "intermediate": "Intermediate",
        "advanced": "Advanced",
    }
    level_display = level_map.get(current_level, "Beginner")

    # Determine exam/goal based on roadmap type
    if roadmap_type == "study":
        exam_goal = target_exam
    elif roadmap_type == "project":
        exam_goal = project_type
    else:
        exam_goal = career_goal

    # Calculate exam date from timeline
    from datetime import datetime, timedelta

    timeline_days = {"1month": 30, "3months": 90, "6months": 180, "1year": 365}
    days = timeline_days.get(timeline, 180)
    exam_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    # Generate roadmap using ML module
    try:
        roadmap = generate_ml_roadmap(
            exam_goal, current_level, exam_date, current_user.id
        )

        if not roadmap:
            return jsonify(
                {
                    "success": False,
                    "error": "ML roadmap model is not trained yet. Please train the model first.",
                }
            ), 503
    except Exception as e:
        return jsonify(
            {"success": False, "error": f"Error generating ML roadmap: {str(e)}"}
        ), 500

    # Generate HTML for the roadmap
    html = generate_roadmap_html(roadmap, roadmap_type)

    return jsonify(
        {
            "success": True,
            "roadmap": {
                "title": roadmap.get("title", f"{exam_goal} Roadmap"),
                "subtitle": f"{level_display} → {timeline_display} • {study_hours} hours/day",
                "meta": f"{len(roadmap.get('phases', []))} Phases • {timeline_display} Goal",
                "diagram": roadmap.get("diagram", ""),
                "html": html,
            },
        }
    )


def convert_to_mermaid(diagram_text):
    """Convert simple diagram text to Mermaid.js flowchart syntax"""
    # If it already has mermaid syntax, just return it
    if "-->" in diagram_text or "graph" in diagram_text.lower():
        return diagram_text

    # Parse simple format like: Start -> Step1 -> Step2 -> End
    # First split by ->
    parts = [p.strip() for p in diagram_text.split("->")]

    # Remove any remaining arrows in parts
    parts = [p.replace("->", "").strip() for p in parts]

    lines = ["graph TD"]
    for i, part in enumerate(parts):
        # Create node ID and label
        node_id = chr(65 + i)  # A, B, C...
        label = part.strip()
        if not label:
            continue
        lines.append(f'    {node_id}["{label}"]')
        if i > 0:
            prev_id = chr(65 + i - 1)
            lines.append(f"    {prev_id} --> {node_id}")

    return "\n".join(lines)


def generate_roadmap_html(roadmap, roadmap_type):
    """Generate HTML for the roadmap with actionable phases, diagram, and print button"""
    html = ""

    # Add diagram section if available - Using Mermaid.js
    diagram = roadmap.get("diagram", "")
    if diagram:
        # Convert simple diagram text to Mermaid format
        mermaid_code = convert_to_mermaid(diagram)
        html += f"""
        <div class="card border-0 shadow-sm mb-4">
            <div class="card-body p-4">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="mb-0"><i class="fa fa-sitemap text-primary me-2"></i>📊 Your Learning Path</h5>
                    <button class="btn btn-outline-primary btn-sm" onclick="window.print()">
                        <i class="fa fa-print me-1"></i>🖨️ Print Roadmap
                    </button>
                </div>
                <div class="roadmap-diagram bg-light p-3 rounded">
                    <div class="mermaid text-center">
                        {mermaid_code}
                    </div>
                </div>
                <small class="text-muted mt-2 d-block">
                    <i class="fa fa-info-circle me-1"></i>This flowchart shows your learning journey. Each step builds on the previous one!
                </small>
            </div>
        </div>
        """

    for idx, phase in enumerate(roadmap["phases"]):
        important_class = "important" if phase.get("important") else ""

        html += f"""
        <div class="roadmap-phase">
            <div class="card phase-card border-0 shadow-sm mb-4">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <div>
                            <span class="badge bg-primary mb-2">{phase["phase"]}</span>
                            <h4 class="mb-1">{phase["goal"]}</h4>
                            <p class="text-muted mb-0"><i class="fa fa-clock me-1"></i> {phase["duration"]}</p>
                        </div>
                        <div class="badge bg-{"danger" if phase.get("important") else "secondary"} fs-6">
                            {"⭐ Important" if phase.get("important") else "Phase " + str(idx + 1)}
                        </div>
                    </div>
                    
                    <h6 class="mb-3"><i class="fa fa-tasks text-primary me-2"></i>What you need to do:</h6>
                    <div class="task-list mb-4">
        """

        for task in phase["tasks"]:
            html += f'<div class="task-item {important_class}">{task}</div>'

        html += f"""
                    </div>
                    
                    <div class="output-box">
                        <h6 class="mb-2"><i class="fa fa-check-circle text-primary me-2"></i>📤 Your Output:</h6>
                        <p class="mb-0 fw-bold">{phase["output"]}</p>
                    </div>
                </div>
            </div>
        </div>
        """

    # Add summary section
    html += f"""
    <div class="card border-0 shadow-sm bg-light">
        <div class="card-body p-4">
            <h5 class="mb-3">📋 Roadmap Summary</h5>
            <div class="row">
                <div class="col-md-4 mb-3">
                    <div class="d-flex align-items-center">
                        <div class="bg-primary rounded-circle p-2 me-3">
                            <i class="fa fa-list text-white"></i>
                        </div>
                        <div>
                            <h6 class="mb-0">{len(roadmap["phases"])} Phases</h6>
                            <small class="text-muted">Structured learning path</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="d-flex align-items-center">
                        <div class="bg-success rounded-circle p-2 me-3">
                            <i class="fa fa-check text-white"></i>
                        </div>
                        <div>
                            <h6 class="mb-0">Actionable Tasks</h6>
                            <small class="text-muted">Clear what to do</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="d-flex align-items-center">
                        <div class="bg-warning rounded-circle p-2 me-3">
                            <i class="fa fa-bullseye text-white"></i>
                        </div>
                        <div>
                            <h6 class="mb-0">Defined Outputs</h6>
                            <small class="text-muted">Know your progress</small>
                        </div>
                    </div>
                </div>
            </div>
            <div class="alert alert-info mt-3 mb-0">
                <i class="fa fa-lightbulb me-2"></i>
                <strong>Pro Tip:</strong> Use the <a href="/timetable">AI Study Planner</a> to create a daily timetable based on this roadmap!
            </div>
        </div>
    </div>
    """

    return html
