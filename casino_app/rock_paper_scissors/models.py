from django.db import models
from django.conf import settings
from decimal import Decimal


class RockPaperScissorsGame(models.Model):
    CHOICES = [
        ('rock', 'Pierre'),
        ('paper', 'Papier'),
        ('scissors', 'Ciseaux'),
    ]
    STATUS_CHOICES = [
        ('waiting', 'En attente'),
        ('playing', 'En cours'),
        ('finished', 'Terminé'),
    ]

    player1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rps_games_as_player1')
    player2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rps_games_as_player2', null=True, blank=True)
    bet_amount = models.DecimalField(max_digits=10, decimal_places=2)
    player1_choice = models.CharField(max_length=10, choices=CHOICES, null=True, blank=True)
    player2_choice = models.CharField(max_length=10, choices=CHOICES, null=True, blank=True)
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='rps_wins')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Game {self.id}: {self.player1} vs {self.player2 or 'Waiting'}"

    def determine_winner(self):
        if not self.player1_choice or not self.player2_choice:
            return None
        if self.player1_choice == self.player2_choice:
            return 'draw'
        rules = {
            'rock': 'scissors',
            'scissors': 'paper',
            'paper': 'rock'
        }
        if rules[self.player1_choice] == self.player2_choice:
            return self.player1
        else:
            return self.player2

    def payout(self):
        from casino_app.wallet.models import Wallet
        total_pot = self.bet_amount * 2
        winnings = total_pot * Decimal('0.8')  # 80% of pot
        house_cut = total_pot - winnings

        winner_wallet = Wallet.objects.get(utilisateur=self.winner)
        winner_wallet.credit(winnings, f"Gagné au Pierre-Papier-Ciseaux contre {self.player2 if self.winner == self.player1 else self.player1}")

        # Optionally log house cut, but since no house wallet, maybe just note it