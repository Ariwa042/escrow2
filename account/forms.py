from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from .models import User, UserProfile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            #'placeholder': 'Enter your email address'
        })
    )
    username = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            #'placeholder': 'Enter your username'
        })
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
           # 'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            #'placeholder': 'Enter your last name'
        })
    )
    password1 = forms.CharField(
        label="Password", 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            #'placeholder': 'Enter your password'
        })
    )
    password2 = forms.CharField(
        label="Confirm Password", 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            #'placeholder': 'Confirm your password'
        })
    )

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email
class UserProfileForm(forms.ModelForm):
    
    phone_number = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = ['phone_number']

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
        return profile


class OTPVerificationForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        required=True,
        label='Enter your OTP',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter OTP'})
    )

    def clean_otp_code(self):
        otp_code = self.cleaned_data.get('otp_code')
        if not otp_code.isdigit() or len(otp_code) != 6:
            raise forms.ValidationError("Enter a valid 6-digit OTP.")
        return otp_code


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'})
    )

    class Meta:
        fields = ['email']

        