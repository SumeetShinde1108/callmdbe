"""
Template-based views for authentication.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import User


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                
                # Handle remember me
                if not remember_me:
                    request.session.set_expiry(0)
                
                messages.success(request, f'Welcome back, {user.name}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Your account is inactive. Please contact support.')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'auth/login.html')


def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            company = request.POST.get('company', '')
            
            # Validation
            if password != password2:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'auth/register.html')
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, 'A user with this email already exists.')
                return render(request, 'auth/register.html')
            
            # Validate password strength
            try:
                validate_password(password)
            except ValidationError as e:
                messages.error(request, ' '.join(e.messages))
                return render(request, 'auth/register.html')
            
            # Create user
            user = User.objects.create_user(
                email=email,
                password=password,
                name=name,
                company=company,
                is_active=True,  # Auto-activate for demo
                role='user'  # Default role
            )
            
            # Auto login after registration
            login(request, user)
            
            messages.success(request, 'Account created successfully! Welcome to CallFairy.')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'auth/register.html')


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def password_reset_request_view(request):
    """Request password reset - sends email with reset link via Celery."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL
            reset_url = request.build_absolute_uri(
                f'/password-reset-confirm/{uid}/{token}/'
            )
            
            # Send email asynchronously via Celery
            from .tasks import send_password_reset_email
            
            try:
                # Queue the email sending task
                task = send_password_reset_email.delay(
                    user_email=user.email,
                    user_name=user.name,
                    reset_url=reset_url
                )
                
                messages.success(
                    request, 
                    'Password reset link is being sent to your email. Please check your inbox in a few moments.'
                )
                
                # Log the task ID for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Password reset email task queued: {task.id} for user {user.email}")
                
            except Exception as e:
                # If Celery fails, show the link on screen for development
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to queue password reset email: {str(e)}")
                messages.warning(
                    request, 
                    f'Email system is currently unavailable. Use this link to reset password: {reset_url}'
                )
            
            return redirect('login')
            
        except User.DoesNotExist:
            # Don't reveal if user exists or not (security best practice)
            messages.success(
                request, 
                'If an account exists with that email, a password reset link has been sent.'
            )
            return redirect('login')
    
    return render(request, 'auth/password_reset_request.html')


def password_reset_confirm_view(request, uidb64, token):
    """Confirm password reset with token."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            
            if password != password2:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'auth/password_reset_confirm.html', {'valid_link': True})
            
            # Validate password strength
            try:
                validate_password(password, user)
            except ValidationError as e:
                messages.error(request, ' '.join(e.messages))
                return render(request, 'auth/password_reset_confirm.html', {'valid_link': True})
            
            # Set new password
            user.set_password(password)
            user.save()
            
            messages.success(request, 'Your password has been reset successfully. You can now login.')
            return redirect('login')
        
        return render(request, 'auth/password_reset_confirm.html', {'valid_link': True})
    else:
        messages.error(request, 'Invalid or expired password reset link.')
        return render(request, 'auth/password_reset_confirm.html', {'valid_link': False})
