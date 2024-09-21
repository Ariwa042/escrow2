from django.contrib import admin
from .models import Cryptocoin, Transaction, Deposit, Withdrawal, Trade, EscrowAgreement

@admin.register(Cryptocoin)
class CryptocoinAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'wallet_address')
    search_fields = ('name', 'symbol')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'crypto_coin', 'amount', 'type', 'status', 'escrow_fee_payer', 'created_at')
    list_filter = ('status', 'type', 'created_at')
    search_fields = ('user__email', 'crypto_coin__name', 'type')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('deposit_id', 'user', 'crypto_coin', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('deposit_id', 'user__email', 'crypto_coin__name')
    readonly_fields = ('created_at',)

@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('withdraw_id', 'user', 'crypto_coin', 'amount', 'destination_address', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('withdraw_id', 'user__email', 'crypto_coin__name', 'destination_address')
    readonly_fields = ('created_at',)

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('trade_id', 'seller_email', 'buyer_email', 'buyer_crypto_coin', 'buyer_token_quantity', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('seller_email', 'buyer_email', 'trade_id', 'buyer_crypto_coin__name')
    readonly_fields = ('created_at',)

@admin.register(EscrowAgreement)
class EscrowAgreementAdmin(admin.ModelAdmin):
    list_display = ('trade', 'escrow_amount', 'release_date', 'release', 'dispute_open', 'created_at')
    list_filter = ('release', 'dispute_open', 'created_at')
    search_fields = ('trade__trade_id',)
    readonly_fields = ('created_at', 'updated_at')