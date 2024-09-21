from django.contrib import admin
from .models import User, UserProfile  # Import your models directly

class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'last_login']

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp_code', 'account_balance']

admin.site.register(User, UserAdmin)  # Correct the model name here
admin.site.register(UserProfile, UserProfileAdmin)  # Correct the model name here
