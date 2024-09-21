from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout as auth_logout
from django.contrib.auth.decorators import login_required

from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode  # Add this import
from django.utils.encoding import force_bytes, force_str 
from django.http import JsonResponse


from django.contrib.auth.forms import AuthenticationForm  # Add this import
from django.contrib.auth.views import PasswordResetView
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

import random

from .forms import CustomPasswordResetForm, OTPVerificationForm, UserRegistrationForm, UserProfileForm
from .models import User, UserProfile
from core.views import dashboard

# Registration view
# Registration view
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account until verified
            user.save()

            # Generate OTP for registration
            otp_code = random.randint(100000, 999999)
            UserProfile.objects.create(user=user, otp_code=otp_code)
            request.session['email'] = user.email

            # Send OTP via email
            send_otp_email(user.email, otp_code)
            messages.success(request, 'Registration successful! Check your email for the OTP verification.')
            return redirect('account:verify_otp')  # Redirect to OTP verification
    else:
        form = UserRegistrationForm()

    return render(request, 'account/register.html', {'form': form})



def verify_otp(request):
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp_code')  # Get the entered OTP

            try:
                # Check if the entered OTP matches the one in the UserProfile
                user_profile = UserProfile.objects.get(otp_code=otp_code)
                user = user_profile.user

                if not user.is_active:  # Case for new user registration
                    user.is_active = True  # Activate the user
                    user.save()

                    user_profile.otp_code = None  # Clear OTP after successful verification
                    user_profile.save()

                    login(request, user)  # Log the user in
                    messages.success(request, 'Your account has been verified successfully!')
                    return redirect('core:dashboard')  # Redirect to dashboard or home page

                else:  # Case for password recovery OTP verification
                    user_profile.otp_code = None  # Clear OTP after successful verification
                    user_profile.save()

                    # Redirect to password reset page for this user
                    return redirect('account:reset_password', user_id=user.id)

            except UserProfile.DoesNotExist:
                # Handle case where OTP is invalid
                messages.error(request, 'Invalid OTP! Please try again.')
    else:
        form = OTPVerificationForm()

    return render(request, 'account/verify_otp.html', {'form': form})


# Function to send the OTP email via Gmail SMTP
def send_otp_email(email, otp_code):
    subject = 'Your OTP Verification Code'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]

    # Create plain text content as a fallback
    text_content = f'Your OTP verification code is {otp_code}. Please enter this code to verify your account.'

    # Render HTML template for the email body
    html_content = render_to_string('emails/otp_email.html', {'otp_code': otp_code})

    # Create the email object with both plain text and HTML
    email_message = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
    email_message.attach_alternative(html_content, "text/html")

    # Send the email
    email_message.send()
    
# Login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('core:dashboard')  # Redirect to your dashboard or home page
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'account/login.html', {'form': form})

# User dashboard view

@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('core:dashboard')  # Use the name of the URL pattern instead of importing the view
    else:
        form = UserProfileForm(instance=user_profile)
    return render(request, 'account/profile.html', {'form': form})

# Logout view
def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('account:login')  # Redirect to login page


#password Reset
def password_recovery(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                otp_code = random.randint(100000, 999999)
                user_profile = user.userprofile
                user_profile.otp_code = otp_code
                user_profile.save()

                # Send OTP email via Gmail SMTP
                send_otp_email(user.email, otp_code)
                messages.success(request, 'Password reset OTP sent! Check your email for verification.')
                return redirect('account:verify_otp')  # Redirect to OTP verification page
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address.')
                return redirect('password_recovery')
    else:
        form = CustomPasswordResetForm()

    return render(request, 'account/password_recovery.html', {'form': form})


def reset_password(request, user_id):
    user = User.objects.get(id=user_id)

    if request.method == "POST":
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password == confirm_password:
            user.set_password(password)
            user.save()
            messages.success(request, 'Password has been reset successfully!')
            return redirect('account:login')
        else:
            messages.error(request, 'Passwords do not match.')

    return render(request, 'account/reset_password.html', {'user': user})


def resend_otp(request):
    if request.method == 'POST':
        # Assuming the user's email is in the session from the original registration process
        email = request.session.get('email')

        if email:
            try:
                # Get the user by the email
                user = get_user_model().objects.get(email=email)
                user_profile = UserProfile.objects.get(user=user)  # Get the user profile associated with the user

                # Generate a new OTP
                new_otp = random.randint(100000, 999999)
                user_profile.otp_code = new_otp
                user_profile.save()  # Save the new OTP to the user's profile

                # Send the new OTP via email
                send_otp_email(user.email, new_otp)

                # Provide a success response
                return JsonResponse({'success': True, 'message': 'A new OTP has been sent to your email.'})

            except get_user_model().DoesNotExist:
                return JsonResponse({'success': False, 'message': 'No account found with the given email address.'})
        else:
            return JsonResponse({'success': False, 'message': 'Email session not found. Please try registering again.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
