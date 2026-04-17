"""
Main Routes - Home, About, Contact pages
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash  # type: ignore[import]
from flask_login import login_required, current_user  # type: ignore[import]
from models import Course, Enrollment  # type: ignore[attr-defined]
from extensions import db  # type: ignore[import]

main = Blueprint("main", __name__)


@main.route("/")
def index():
    """Home page - shows featured courses or redirects to dashboard if logged in"""
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    courses = Course.query.filter_by(is_published=True).all()

    # Fetch published tests for the mock test series section
    from models import Test

    tests = Test.query.filter_by(is_published=True).limit(6).all()

    return render_template("index.html", courses=courses, tests=tests)


@main.route("/about")
def about():
    """About page"""
    return render_template("about.html")


@main.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact page"""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        # Here you would save the contact message or send an email
        flash("Thank you for contacting us! We will get back to you soon.", "success")
        return redirect(url_for("main.contact"))

    return render_template("contact.html")


@main.route("/team")
def team():
    """Team/Instructors page"""
    return render_template("team.html")


@main.route("/testimonial")
def testimonial():
    """Testimonials page"""
    return render_template("testimonial.html")


@main.route("/courses")
def all_courses():
    """All courses page with filtering"""
    from flask_login import current_user
    from models import Category, Enrollment

    category = request.args.get("category")

    query = Course.query.filter_by(is_published=True)

    if category:
        query = query.filter_by(category=category)

    courses = query.order_by(Course.created_at.desc()).all()

    # Get proper category objects for the grid
    categories = (
        Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
    )

    # Get user's enrolled course IDs if logged in
    enrolled_course_ids = []
    if current_user.is_authenticated:
        enrollments = Enrollment.query.filter_by(
            user_id=current_user.id, status="active"
        ).all()
        enrolled_course_ids = [e.course_id for e in enrollments]

    return render_template(
        "courses.html",
        courses=courses,
        categories=categories,
        current_category=category,
        enrolled_course_ids=enrolled_course_ids,
    )
