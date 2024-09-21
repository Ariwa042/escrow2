from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('join_trade/', views.join_trade, name='join_trade'),
    path('trade_detail/<str:trade_id>/', views.trade_detail, name='trade_detail'),
    path('trade_history/', views.trade_history, name='trade_history'),
    path('create_trade/', views.create_trade, name='create_trade'),
    path('accept_trade/<int:trade_id>/', views.accept_trade, name='accept_trade'),
    path('release_escrow/<int:trade_id>/', views.release_escrow, name='release_escrow'),
    path('open_dispute/<int:trade_id>/', views.open_dispute, name='open_dispute'),
    path('create_deposit/', views.create_deposit, name='create_deposit'),
    path('create_withdrawal/', views.create_withdrawal, name='create_withdrawal'),
    path('transaction_history/', views.transaction_history, name='transaction_history'),
    path('trade_success/<int:trade_id>/', views.trade_success, name='trade_success'),
 #   path('trade_error/', views.trade_error, name='trade_error'),
    path('deposit_success/', views.deposit_success, name='deposit_success'),
    path('deposit-instructions/', views.deposit_instructions, name='deposit_instructions'),
    path('withdrawal_success/', views.withdrawal_success, name='withdrawal_success'),
    path('about/', views.about, name='about'),
    #path('mark-deposit-as-paid/<int:deposit_id>', views.mark_deposit_as_paid, name='mark_deposit_as_paid'),
]