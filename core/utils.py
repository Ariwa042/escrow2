# utils.py

from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.template.loader import render_to_string
import qrcode
import io
import base64
from io import BytesIO

def send_email(subject, message, recipient_list):
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

def send_trade_invitation_email(buyer_email, seller_email, trade):
    subject = "Trade Invitation"
    for recipient_email in [buyer_email, seller_email]:
        role = 'BUYER' if recipient_email == buyer_email else 'SELLER'
        context = {
            'trade': trade,
            'recipient_role': role,
            'recipient_email': recipient_email,
            'trade_url': settings.BASE_URL + reverse('core:trade_detail', args=[trade.trade_id])
        }
        html_content = render_to_string('emails/trade_invitation_email.html', context)
        text_content = f"You have been invited to participate in a trade as a {role.lower()}. Trade ID: {trade.trade_id}."
        send_mail(subject, text_content, settings.DEFAULT_FROM_EMAIL, [recipient_email], html_message=html_content)

def send_escrow_created_email(seller_email, buyer_email, escrow):
    subject = "Escrow Agreement Created"
    context = {
        'escrow': escrow,
        'trade_url': settings.BASE_URL + reverse('core:trade_detail', args=[escrow.trade.trade_id])
    }
    html_content = render_to_string('emails/escrow_created_email.html', context)
    text_content = f"An escrow agreement has been created for your trade. Escrow ID: {escrow.id}"
    send_mail(subject, text_content, settings.DEFAULT_FROM_EMAIL, [seller_email, buyer_email], html_message=html_content)

def send_deposit_confirmation_email(user_email, deposit):
    subject = "Deposit Confirmation"
    context = {
        'deposit': deposit,
        'transaction_url': settings.BASE_URL + reverse('core:transaction_history')
    }
    html_content = render_to_string('emails/deposit_confirmation_email.html', context)
    text_content = f"Your deposit of {deposit.amount} {deposit.crypto_coin} has been received and is pending confirmation."
    send_mail(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user_email], html_message=html_content)

def send_withdrawal_confirmation_email(user_email, withdrawal):
    subject = "Withdrawal Confirmation"
    context = {
        'withdrawal': withdrawal,
        'transaction_url': settings.BASE_URL + reverse('core:transaction_history')
    }
    html_content = render_to_string('emails/withdrawal_confirmation_email.html', context)
    text_content = f"Your withdrawal request for {withdrawal.amount} {withdrawal.crypto_coin} has been received and is being processed."
    send_mail(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user_email], html_message=html_content)

def send_deposit_status_update_email(user_email, deposit):
    subject = "Deposit Status Update"
    context = {
        'deposit': deposit,
        'transaction_url': settings.BASE_URL + reverse('core:transaction_history')
    }
    html_content = render_to_string('emails/deposit_status_update_email.html', context)
    text_content = f"The status of your deposit of {deposit.amount} {deposit.crypto_coin} has been updated to {deposit.status}."
    send_mail(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user_email], html_message=html_content)

def send_withdrawal_status_update_email(user_email, withdrawal):
    subject = "Withdrawal Status Update"
    context = {
        'withdrawal': withdrawal,
        'transaction_url': settings.BASE_URL + reverse('core:transaction_history')
    }
    html_content = render_to_string('emails/withdrawal_status_update_email.html', context)
    text_content = f"The status of your withdrawal of {withdrawal.amount} {withdrawal.crypto_coin} has been updated to {withdrawal.status}."
    send_mail(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user_email], html_message=html_content)


def generate_qr_code(wallet_address):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(wallet_address)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return qr_code_base64
