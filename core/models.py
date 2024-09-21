from django.conf import settings
from django.db import models
from django.utils import timezone
from shortuuid.django_fields import ShortUUIDField
from django.db.models.signals import pre_save, post_save
from django.db.models.signals import post_save, pre_save
from .utils import (
    send_deposit_confirmation_email,
    send_withdrawal_confirmation_email,
    send_deposit_status_update_email,
    send_withdrawal_status_update_email
)
from django.dispatch import receiver
from django.db.models import F
from account.models import User, UserProfile
import random

User = settings.AUTH_USER_MODEL

STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('COMPLETED', 'Completed'),
    ('FAILED', 'Failed'),
]

TYPE_CHOICES = [
    ('DEPOSIT', 'Deposit'),
    ('WITHDRAWAL', 'Withdrawal'),
]

ESCROW_FEE_PAYER = [
    ('BUYER', 'Buyer'),
    ('SELLER', 'Seller'),
    ('BOTH', '50/50'),
]

ROLE_CHOICES = [
    ('BUYER', 'Buyer'),
    ('SELLER', 'Seller'),
]


class Cryptocoin(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, unique=True)
    wallet_address = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='cryptocoins/', null=True, blank=True)


    def __str__(self):
        return f'{self.name} ({self.symbol})'


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    crypto_coin = models.ForeignKey(Cryptocoin, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              default='PENDING')
    escrow_fee_payer = models.CharField(max_length=20,
                                        choices=ESCROW_FEE_PAYER,
                                        default='BOTH',
                                        null=True,
                                        blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.crypto_coin} {self.amount} {self.type} by {self.user}'


class Deposit(models.Model):
    deposit_id = ShortUUIDField(unique=True, length=10, max_length=15)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    crypto_coin = models.ForeignKey(Cryptocoin, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              default='PENDING')

    def __str__(self):
        return f"Deposit of {self.amount} {self.crypto_coin} by {self.user} ({self.status})"


class Withdrawal(models.Model):
    WITHDRAWAL_METHOD_CHOICES = [
        ('crypto', 'Cryptocurrency'),
        ('bank', 'Bank Transfer'),
    ]

    withdraw_id = ShortUUIDField(unique=True, length=10, max_length=15)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    crypto_coin = models.ForeignKey(Cryptocoin, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    destination_address = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=20, null=True, blank=True)
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    withdrawal_method = models.CharField(max_length=10, choices=WITHDRAWAL_METHOD_CHOICES, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Withdrawal of {self.amount} {self.crypto_coin} by {self.user.username} ({self.status})"


class Trade(models.Model):
    ESCROW_FEE_PAYER = [
        ('BUYER', 'Buyer'),
        ('SELLER', 'Seller'),
        ('BOTH', '50/50'),
    ]
    
    trade_id = models.CharField(max_length=5, unique=True, editable=False)
    buyer_email = models.EmailField()
    seller_email = models.EmailField()
    buyer_crypto_coin = models.ForeignKey(Cryptocoin,
                                          related_name='buyer_crypto',
                                          on_delete=models.CASCADE)
    buyer_token_quantity = models.DecimalField(max_digits=20, decimal_places=8)
    seller_crypto_coin = models.ForeignKey(Cryptocoin,
                                           related_name='seller_crypto',
                                           on_delete=models.CASCADE)
    seller_token_quantity = models.DecimalField(max_digits=20,
                                                decimal_places=8)
    escrow_fee_payer = models.CharField(max_length=20,
                                        choices=ESCROW_FEE_PAYER,
                                        default='BOTH')
    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              default='PENDING')
    created_at = models.DateTimeField(default=timezone.now)
    buyer_deposit_status = models.CharField(max_length=20,
                                            choices=STATUS_CHOICES,
                                            default='PENDING')
    seller_deposit_status = models.CharField(max_length=20,
                                             choices=STATUS_CHOICES,
                                             default='PENDING')
    fee_payment_status = models.CharField(max_length=20,
                                          choices=STATUS_CHOICES,
                                          default='PENDING')

    def save(self, *args, **kwargs):
        if not self.trade_id:
            self.trade_id = ''.join(
                [str(random.randint(0, 9)) for _ in range(5)])
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Trade {self.trade_id}: {self.buyer_email} buys from {self.seller_email}'


class EscrowAgreement(models.Model):
    trade = models.OneToOneField(Trade, on_delete=models.CASCADE)
    escrow_amount = models.DecimalField(max_digits=20, decimal_places=8)
    release_date = models.DateTimeField(default=timezone.now)
    release = models.BooleanField(default=False)
    dispute_open = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Escrow agreement for trade {self.trade.trade_id}'

    def release_funds(self):
        if not self.release and timezone.now() >= self.release_date:
            self.trade.status = 'COMPLETED'
            self.trade.save()
            self.release = True
            self.save()


@receiver(pre_save, sender=Deposit)
def update_balance_on_deposit(sender, instance, **kwargs):
    if instance.id:
        old_instance = Deposit.objects.get(id=instance.id)
        if old_instance.status != 'COMPLETED' and instance.status == 'COMPLETED':
            user_profile = UserProfile.objects.get(user=instance.user)
            user_profile.account_balance += instance.amount
            user_profile.save()


@receiver(pre_save, sender=Withdrawal)
def update_balance_on_withdrawal(sender, instance, **kwargs):
    if instance.id:
        old_instance = Withdrawal.objects.get(id=instance.id)
        if old_instance.status != 'COMPLETED' and instance.status == 'COMPLETED':
            user_profile = UserProfile.objects.get(user=instance.user)
            if user_profile.account_balance >= instance.amount:
                user_profile.account_balance -= instance.amount
                user_profile.save()
            else:
                raise ValueError("Insufficient balance to process withdrawal")
                
@receiver(post_save, sender=Deposit)
def send_deposit_email(sender, instance, created, **kwargs):
    if created:
        send_deposit_confirmation_email(instance.user.email, instance)
    else:
        send_deposit_status_update_email(instance.user.email, instance)

@receiver(post_save, sender=Withdrawal)
def send_withdrawal_email(sender, instance, created, **kwargs):
    if created:
        send_withdrawal_confirmation_email(instance.user.email, instance)
    else:
        send_withdrawal_status_update_email(instance.user.email, instance)

