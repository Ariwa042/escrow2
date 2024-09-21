from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('password_recovery/',
         views.password_recovery,
         name='password_recovery'),
    path('reset_password/<int:user_id>/',
         views.reset_password,
         name='reset_password'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('send_otp/', views.send_otp_email, name='send_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
]
