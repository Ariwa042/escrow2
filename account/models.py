from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
#    is_active = models.BooleanField(default=False)
 #   is_staff = models.BooleanField(default=False)
  #  is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    class Meta:
      verbose_name = 'User'
      verbose_name_plural = 'Users'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    last_otp_sent = models.DateTimeField(null=True, blank=True)  # Timestamp for when the last OTP was sent
    def can_resend_otp(self):
        if self.last_otp_sent is None:
            return True
        cooldown_period = timezone.timedelta(minutes=2)
        return timezone.now() >= self.last_otp_sent + cooldown_period

    def update_last_otp_sent(self):
        self.last_otp_sent = timezone.now()
        self.save()
        
    def __str__(self):
        return f'Profile of {self.user.username}'

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

#account.models