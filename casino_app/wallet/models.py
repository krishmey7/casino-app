from decimal import Decimal
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone


class Wallet(models.Model):
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'

    def __str__(self):
        return f"Wallet({self.utilisateur.username}): {self.balance}"

    def _create_tx(self, type_tx, amount, before, after, description=''):
        return Transaction.objects.create(
            utilisateur=self.utilisateur,
            wallet=self,
            type_transaction=type_tx,
            montant=amount,
            solde_avant=before,
            solde_apres=after,
            description=description,
            date_transaction=timezone.now()
        )

    def credit(self, amount, description='Crédit'):
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError('Amount must be positive')

        with transaction.atomic():
            w = Wallet.objects.select_for_update().get(pk=self.pk)
            before = w.balance
            w.balance = (w.balance + amount)
            w.save(update_fields=['balance', 'updated_at'])
            tx = w._create_tx('depot', amount, before, w.balance, description)
        return w.balance, tx

    def debit(self, amount, description='Débit'):
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError('Amount must be positive')

        with transaction.atomic():
            w = Wallet.objects.select_for_update().get(pk=self.pk)
            before = w.balance
            if w.balance < amount:
                raise ValueError('Solde insuffisant')
            w.balance = (w.balance - amount)
            w.save(update_fields=['balance', 'updated_at'])
            tx = w._create_tx('mise', amount, before, w.balance, description)
        return w.balance, tx


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('depot', 'Dépôt'),
        ('retrait', 'Retrait'),
        ('mise', 'Mise'),
        ('gain', 'Gain'),
        ('commission', 'Commission'),
    ]

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet_transactions')
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    type_transaction = models.CharField(max_length=20, choices=TYPE_CHOICES)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    solde_avant = models.DecimalField(max_digits=12, decimal_places=2)
    solde_apres = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    date_transaction = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-date_transaction']

    def __str__(self):
        return f"{self.type_transaction} {self.montant} for {self.utilisateur.username} at {self.date_transaction}"