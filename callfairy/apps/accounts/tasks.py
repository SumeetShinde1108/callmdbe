"""
Celery tasks for email sending and authentication.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_email, user_name, reset_url):
    """
    Send password reset email asynchronously via Celery.
    
    Args:
        user_email: Email address to send to
        user_name: Name of the user
        reset_url: Password reset URL
    """
    try:
        subject = 'Password Reset - CallFairy'
        message = f'''Hi {user_name},

You requested a password reset for your CallFairy account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Thanks,
CallFairy Team'''

        # HTML version (optional, looks better)
        html_message = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #7c3aed;">CallFairy Password Reset</h2>
                <p>Hi <strong>{user_name}</strong>,</p>
                <p>You requested a password reset for your CallFairy account.</p>
                <p>Click the button below to reset your password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #7c3aed; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    Or copy and paste this link into your browser:<br>
                    <a href="{reset_url}" style="color: #7c3aed;">{reset_url}</a>
                </p>
                <p style="color: #666; font-size: 14px;">
                    This link will expire in 24 hours.
                </p>
                <p style="color: #666; font-size: 14px;">
                    If you didn't request this, please ignore this email.
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    Thanks,<br>
                    CallFairy Team
                </p>
            </div>
        </body>
        </html>
        '''

        # Send email
        result = send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        
        if result == 1:
            logger.info(f"Password reset email sent successfully to {user_email}")
            return {
                'status': 'success',
                'message': f'Email sent to {user_email}',
                'email': user_email
            }
        else:
            logger.error(f"Failed to send password reset email to {user_email}")
            raise Exception("Email sending failed")
            
    except Exception as e:
        logger.error(f"Error sending password reset email to {user_email}: {str(e)}")
        
        # Retry up to 3 times with exponential backoff
        try:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for password reset email to {user_email}")
            return {
                'status': 'error',
                'message': str(e),
                'email': user_email
            }


@shared_task
def send_welcome_email(user_email, user_name):
    """
    Send welcome email to new users.
    
    Args:
        user_email: Email address to send to
        user_name: Name of the user
    """
    try:
        subject = 'Welcome to CallFairy!'
        message = f'''Hi {user_name},

Welcome to CallFairy! We're excited to have you on board.

You can now start making AI-powered voice calls to your contacts.

Get started:
- Add your contacts
- Create your first call
- Set up bulk calling campaigns

If you have any questions, feel free to reach out.

Thanks,
CallFairy Team'''

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=True,
        )
        
        logger.info(f"Welcome email sent to {user_email}")
        return {'status': 'success', 'email': user_email}
        
    except Exception as e:
        logger.error(f"Error sending welcome email to {user_email}: {str(e)}")
        return {'status': 'error', 'message': str(e)}
