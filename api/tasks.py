from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags

try:
    from celery import shared_task
    CELERY_AVAILABLE = settings.CELERY_ENABLED
except ImportError:
    CELERY_AVAILABLE = False


def _send_welcome_email(user_email, first_name):
    """
    Internal helper to send the welcome email (HTML + plain text fallback)
    """
    subject = "🎉 Welcome to CODED Online Poll System!"
    
    html_message = f"""
    <html>
      <body>
        <p>Hi {first_name},</p>
        <p>Welcome to <strong>Online Poll System</strong>! We're thrilled to have you on board.</p>
        <p>Here’s what you can do next:</p>
        <ul>
          <li>Explore and participate in polls.</li>
          <li>Track your voting history.</li>
          <li>Stay updated with new polls.</li>
        </ul>
        <p>If you have any questions, feel free to reach out to our support team.</p>
        <p>Happy polling! 🗳️</p>
        <p>— The Online Poll System Team</p>
      </body>
    </html>
    """
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [user_email],
        html_message=html_message,
        fail_silently=False,
    )
    return f"Sent welcome email to {user_email}"


# Celery task if available
if CELERY_AVAILABLE:
    @shared_task
    def send_welcome_email(user_email, first_name):
        return _send_welcome_email(user_email, first_name)
else:
    # Fallback: synchronous call
    def send_welcome_email(user_email, first_name):
        return _send_welcome_email(user_email, first_name)
