from django.contrib import admin
from .models import Wallet, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'balance', 'updated_at')
    search_fields = ('utilisateur__username', 'utilisateur__email')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'type_transaction', 'montant', 'solde_avant', 'solde_apres', 'date_transaction')
    list_filter = ('type_transaction',)
    search_fields = ('utilisateur__username',)




