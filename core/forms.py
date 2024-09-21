from django import forms
from django.contrib.auth import get_user_model
from .models import Trade, Deposit, Withdrawal, Cryptocoin

User = get_user_model()

class TradeForm(forms.ModelForm):
    # Define form fields for buyer and seller details
    buyer_email = forms.EmailField(label="Buyer's Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    seller_email = forms.EmailField(label="Seller's Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    buyer_crypto_coin = forms.ModelChoiceField(queryset=Cryptocoin.objects.all(), label="Buyer's Cryptocoin", widget=forms.Select(attrs={'class': 'form-control'}))
    buyer_token_quantity = forms.DecimalField(max_digits=20, decimal_places=8, label="Buyer's Token Quantity", widget=forms.NumberInput(attrs={'step': '0.00000001', 'class': 'form-control'}))
    seller_crypto_coin = forms.ModelChoiceField(queryset=Cryptocoin.objects.all(), label="Seller's Cryptocoin", widget=forms.Select(attrs={'class': 'form-control'}))
    seller_token_quantity = forms.DecimalField(max_digits=20, decimal_places=8, label="Seller's Token Quantity", widget=forms.NumberInput(attrs={'step': '0.00000001', 'class': 'form-control'}))


    # Reference the `COMMISSION_PAYER_CHOICES` directly
    commission_payer = forms.ChoiceField(choices=Trade.ESCROW_FEE_PAYER, label="Who Pays the Escrow Fee", widget=forms.Select(attrs={'class': 'form-control'}))


    class Meta:
        model = Trade
        fields = ['buyer_email', 'seller_email', 'buyer_crypto_coin', 'buyer_token_quantity', 'seller_crypto_coin', 'seller_token_quantity', 'commission_payer']

    def clean(self):
        cleaned_data = super().clean()
        buyer_email = cleaned_data.get('buyer_email')
        seller_email = cleaned_data.get('seller_email')
        buyer_token_quantity = cleaned_data.get('buyer_token_quantity')
        seller_token_quantity = cleaned_data.get('seller_token_quantity')

        # Ensure both emails are provided
        if not buyer_email:
            raise forms.ValidationError("Buyer’s Email is required.")
        if not seller_email:
            raise forms.ValidationError("Seller’s Email is required.")

        # Ensure both token quantities are provided
        if not buyer_token_quantity:
            raise forms.ValidationError("Buyer’s Token Quantity is required.")
        if not seller_token_quantity:
            raise forms.ValidationError("Seller’s Token Quantity is required.")

        return cleaned_data


class DepositForm(forms.ModelForm):
    class Meta:
        model = Deposit
        fields = ['crypto_coin', 'amount']
        widgets = {
            'crypto_coin': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'step': '0.00000001', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')

        # Additional validation: Ensure the deposit amount is positive
        if amount <= 0:
            raise forms.ValidationError("Deposit amount must be greater than zero.")

        return cleaned_data


class WithdrawalForm(forms.ModelForm):
    WITHDRAWAL_METHOD_CHOICES = [
        ('crypto', 'Cryptocurrency'),
        ('bank', 'Bank Transfer'),
    ]

    withdrawal_method = forms.ChoiceField(choices=WITHDRAWAL_METHOD_CHOICES, required=True)
    account_number = forms.CharField(max_length=20, required=False)
    bank_name = forms.CharField(max_length=100, required=False)

    class Meta:
        model = Withdrawal
        fields = ['crypto_coin', 'amount', 'destination_address', 'withdrawal_method', 'account_number', 'bank_name']

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('withdrawal_method')
        account_number = cleaned_data.get('account_number')
        bank_name = cleaned_data.get('bank_name')

        if method == 'bank':
            if not account_number or not bank_name:
                raise forms.ValidationError("Account number and bank name are required for bank transfers.")
        return cleaned_data

class TradeSearchForm(forms.Form):
    trade_id = forms.CharField(max_length=30, label='Trade ID', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Trade ID'}))