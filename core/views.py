from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from .models import Deposit, Withdrawal, Trade, EscrowAgreement, Cryptocoin
from account.models import UserProfile
from .forms import DepositForm, WithdrawalForm, TradeForm, TradeSearchForm
from django.db.models import Q
from .utils import (send_trade_invitation_email, send_escrow_created_email,
                    generate_qr_code)
import logging
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal



# General homepage for non-users
def index(request):
    return render(request, 'core/index.html')


# Transaction History View
@login_required
def transaction_history(request):
    deposits = Deposit.objects.filter(
        user=request.user).order_by('-created_at')
    withdrawals = Withdrawal.objects.filter(
        user=request.user).order_by('-created_at')
    return render(request, 'core/transaction_history.html', {
        'deposits': deposits,
        'withdrawals': withdrawals,
    })


logger = logging.getLogger(__name__)


@login_required
def create_deposit(request):
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            # Store the form data temporarily in the session
            form_data = form.cleaned_data
            request.session['deposit_form_data'] = {
                'crypto_coin_id': form_data.get('crypto_coin').
                id,  # Store the ID instead of the whole object
                'amount': str(form_data.get('amount'))
            }
            return redirect('core:deposit_instructions')
    else:
        form = DepositForm()
    return render(request, 'core/create_deposit.html', {'form': form})


def deposit_instructions(request):
    form_data = request.session.get('deposit_form_data')
    if not form_data:
        return redirect('create_deposit')

    crypto_coin_id = form_data.get('crypto_coin_id')
    try:
        crypto_coin = Cryptocoin.objects.get(id=crypto_coin_id)
    except Cryptocoin.DoesNotExist:
        return redirect('create_deposit')

    amount = Decimal(form_data.get('amount'))
    qr_code = generate_qr_code(crypto_coin.wallet_address)

    if request.method == 'POST':
        # Finalize the deposit
        Deposit.objects.create(
            user=request.user,
            crypto_coin=crypto_coin,
            amount=amount,
            qr_code=qr_code,
            # Add additional fields if needed
        )
        # Clear session data
        request.session.pop('deposit_form_data', None)
        return redirect('core:deposit_success')  # Redirect to a success page

    return render(request, 'core/deposit_instructions.html', {
        'crypto_coin': crypto_coin,
        'amount': form_data.get('amount'),
        'qr_code': qr_code,
    })


# Create Withdrawal View (User creates a withdrawal request)
@login_required
def create_withdrawal(request):
    user_profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            withdrawal = form.save(commit=False)
            withdrawal.user = request.user
            withdrawal_amount = withdrawal.amount

            # Check if the user has enough balance
            if user_profile.account_balance >= withdrawal_amount:
                withdrawal.status = 'PENDING'  # Default status for withdrawal
                withdrawal.save()
                messages.success(
                    request,
                    'Withdrawal request created and is pending admin approval.')
                return redirect('core:withdrawal_success')
            else:
                # Attach error to the form's 'amount' field for insufficient balance
                form.add_error('amount', 'Insufficient balance for this withdrawal.')
    else:
        form = WithdrawalForm()

    return render(request, 'core/create_withdrawal.html', {'form': form})

# Current Trades View (Displays all pending trades)
@login_required
def current_trades(request):
    trades = Trade.objects.filter(status='PENDING').order_by('-created_at')
    return render(request, 'core/current_trades.html', {'trades': trades})


# Join Trade View (Allow a user to join a trade)


@login_required
def join_trade(request):
    if request.method == 'POST':
        form = TradeSearchForm(request.POST)
        if form.is_valid():
            trade_id = form.cleaned_data.get('trade_id')
            try:
                # Try to get the trade object based on the provided trade_id
                trade = Trade.objects.get(trade_id=trade_id)

                # If trade is found, success message and redirect to trade details
                messages.success(request, f'You have accessed the trade {trade_id}.')
                return redirect('core:trade_detail', trade_id=trade_id)

            except Trade.DoesNotExist:
                # If trade does not exist, show an error message
                form.add_error('trade_id', 'This trade ID does not exist.')

    else:
        form = TradeSearchForm()

    return render(request, 'core/join_trade.html', {'form': form})


# Trade History View (Displays trade history for buyer/seller)
@login_required
def trade_history(request):
    trades = Trade.objects.filter(
        Q(buyer_email=request.user.email)
        | Q(seller_email=request.user.email)).order_by('-created_at')

    return render(request, 'core/trade_history.html', {'trades': trades})


# Create Trade View (Allows user to create a trade)
@login_required
@require_http_methods(["GET", "POST"])
def create_trade(request):
    if request.method == 'POST':
        form = TradeForm(request.POST)
        if form.is_valid():
            trade = form.save()
            send_trade_invitation_email(trade.buyer_email, trade.seller_email,
                                        trade)
            return JsonResponse({'success': True, 'trade_id': trade.trade_id})
        else:
            errors = form.errors.as_json()
            return JsonResponse({
                'success': False,
                'error': 'Invalid form data',
                'form_errors': errors
            })
    else:
        form = TradeForm()
    return render(request, 'core/create_trade.html', {'form': form})


# Manage Trade View (Manage and accept/reject trade offers)
@login_required
def manage_trade(request, trade_id):
    trade = get_object_or_404(Trade, trade_id=trade_id)
    if request.user.email not in [trade.buyer_email, trade.seller_email]:
        messages.error(request,
                       'You do not have permission to manage this trade.')
        return redirect('core:current_trades')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            trade.status = 'ACCEPTED'
        elif action == 'reject':
            trade.status = 'REJECTED'
        trade.save()

        if trade.status == 'ACCEPTED':
            escrow = EscrowAgreement.objects.create(
                trade=trade,
                escrow_amount=trade.buyer_token_quantity,
                release_date=timezone.now() + timezone.timedelta(days=7))
            send_escrow_created_email(trade.seller_email, trade.buyer_email,
                                      escrow)

        messages.success(request,
                         f'Trade {action.capitalize()}d successfully!')
        return redirect('core:current_trades')

    return render(request, 'core/manage_trade.html', {'trade': trade})


# Trade Detail View (Show details of a specific trade)
@login_required
def trade_detail(request, trade_id):
    trade = get_object_or_404(Trade, trade_id=trade_id)
    return render(request, 'core/trade_detail.html', {'trade': trade})


# Dashboard View (User overview)
@login_required
def dashboard(request):
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user)
    deposits = Deposit.objects.filter(user=request.user)
    withdrawals = Withdrawal.objects.filter(user=request.user)
    trades = Trade.objects.filter(
        Q(buyer_email=request.user.email) | Q(seller_email=request.user.email))

    return render(
        request, 'core/dashboard.html', {
            'user_profile': user_profile,
            'deposits': deposits,
            'withdrawals': withdrawals,
            'trades': trades,
        })


# Trade Success View
@login_required
def trade_success(request, trade_id):
    trade = get_object_or_404(Trade, trade_id=trade_id)
    messages.success(request, f'Trade {trade_id} created successfully!')
    return redirect('core:dashboard')


# Deposit Success View
def deposit_success(request):
    return render(request, 'core/deposit_success.html')

def withdrawal_success(request):
    return render(request, 'core/withdrawal_success.html')


# Open Dispute
@login_required
@require_POST
def open_dispute(request, trade_id):
    trade = get_object_or_404(Trade, trade_id=trade_id)
    if request.user.email not in [trade.buyer_email, trade.seller_email]:
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    escrow = trade.escrowagreement
    escrow.dispute_open = True
    escrow.save()

    messages.warning(request,
                     'Dispute opened. An admin will review your case.')
    return JsonResponse({'success': True})


# Release Escrow View
@login_required
@require_POST
def release_escrow(request, trade_id):
    trade = get_object_or_404(Trade, trade_id=trade_id)
    if request.user.email != trade.buyer_email:
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    escrow = trade.escrowagreement
    escrow.release_funds()

    messages.success(request, 'Funds released from escrow.')
    return JsonResponse({'success': True})


def accept_trade(request, trade_id):
    trade = get_object_or_404(Trade, trade_id=trade_id)
    if request.user.email not in [trade.buyer_email, trade.seller_email]:
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    trade.status = 'ACCEPTED'
    trade.save()

    escrow = EscrowAgreement.objects.create(
        trade=trade,
        escrow_amount=trade.buyer_token_quantity,
        release_date=timezone.now() + timezone.timedelta(days=7))
    send_escrow_created_email(trade.seller_email, trade.buyer_email, escrow)

    return JsonResponse({'success': True})


def about(request):
    return render(request, 'core/about.html')
 