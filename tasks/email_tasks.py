"""
Email Tasks for Celery
"""

from tasks import celery_app  # type: ignore[import]
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name='send_email')
def send_email(recipient, subject, body, html=None):
    """
    Send an email to a user
    
    Args:
        recipient: Email address of the recipient
        subject: Subject of the email
        body: Plain text body
        html: HTML body (optional)
    """
    try:
        # In production, use Flask-Mail or similar
        # from flask_mail import Message
        # from app import mail
        
        # msg = Message(
        #     subject=subject,
        #     recipients=[recipient],
        #     body=body,
        #     html=html
        # )
        # mail.send(msg)
        
        logger.info(f"Email sent to {recipient}: {subject}")
        return {'status': 'sent', 'recipient': recipient}
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


@celery_app.task(name='send_welcome_email')
def send_welcome_email(user_id, email, first_name):
    """Send welcome email to new users"""
    subject = "Welcome to LearnNova!"
    body = f"""
    Hello {first_name},
    
    Welcome to LearnNova! We're excited to have you on board.
    
    Get started by exploring our courses and connecting with other learners.
    
    Best regards,
    The LearnNova Team
    """
    
    html = f"""
    <html>
    <body>
        <h1>Welcome to LearnNova!</h1>
        <p>Hello {first_name},</p>
        <p>We're excited to have you on board!</p>
        <p>Get started by exploring our courses and connecting with other learners.</p>
        <p>Best regards,<br>The LearnNova Team</p>
    </body>
    </html>
    """
    
    return send_email(email, subject, body, html)


@celery_app.task(name='send_course_enrollment_confirmation')
def send_course_enrollment_confirmation(user_id, email, course_name):
    """Send course enrollment confirmation email"""
    subject = f"Enrolled in {course_name}"
    body = f"""
    Congratulations!
    
    You have successfully enrolled in {course_name}.
    
    Start learning now!
    
    Best regards,
    The LearnNova Team
    """
    
    html = f"""
    <html>
    <body>
        <h1>Congratulations!</h1>
        <p>You have successfully enrolled in <strong>{course_name}</strong>.</p>
        <p>Start learning now!</p>
        <p>Best regards,<br>The LearnNova Team</p>
    </body>
    </html>
    """
    
    return send_email(email, subject, body, html)


@celery_app.task(name='send_progress_reminder')
def send_progress_reminder(user_id, email, course_name, progress):
    """Send progress reminder email"""
    subject = f"Continue your learning in {course_name}"
    body = f"""
    Hi there!
    
    You're {progress}% through {course_name}.
    
    Keep up the great work! Resume your learning now.
    
    Best regards,
    The LearnNova Team
    """
    
    html = f"""
    <html>
    <body>
        <h1>Continue Learning</h1>
        <p>You're <strong>{progress}%</strong> through <strong>{course_name}</strong>.</p>
        <p>Keep up the great work! Resume your learning now.</p>
        <p>Best regards,<br>The LearnNova Team</p>
    </body>
    </html>
    """
    
    return send_email(email, subject, body, html)
