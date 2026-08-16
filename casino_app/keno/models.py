from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class KenoGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='keno_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    picks = models.JSONField(default=list)  # Numéros choisis par le joueur (1-80)
    drawn_numbers = models.JSONField(default=list)  # Numéros tirés
    matches = models.IntegerField(default=0)  # Nombre de correspondances
    
    payout_table = models.JSONField(default=dict)  # Tableau des gains
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    
    result = models.CharField(max_length=10, null=True, blank=True)  # win/lose
    status = models.CharField(max_length=10, default='playing')  # playing/finished
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Keno Game {self.id} - {self.player.username}"

    def generate_payouts(self):
        """Génère la table des gains basée sur les correspondances"""
        picks_count = len(self.picks)
        payouts = {
            0: Decimal('0'),
            1: Decimal('0') if picks_count >= 4 else Decimal('1'),
            2: Decimal('0') if picks_count >= 5 else Decimal('1'),
            3: Decimal('1') if picks_count == 3 else (Decimal('0') if picks_count >= 6 else Decimal('2')),
            4: Decimal('2') if picks_count == 4 else (Decimal('0') if picks_count >= 7 else Decimal('5')),
            5: Decimal('5') if picks_count == 5 else (Decimal('0') if picks_count >= 8 else Decimal('10')),
            6: Decimal('10') if picks_count == 6 else (Decimal('0') if picks_count >= 9 else Decimal('20')),
            7: Decimal('100') if picks_count == 7 else (Decimal('0') if picks_count >= 10 else Decimal('50')),
            8: Decimal('500') if picks_count == 8 else (Decimal('0') if picks_count >= 11 else Decimal('200')),
            9: Decimal('1000') if picks_count == 9 else (Decimal('0') if picks_count >= 12 else Decimal('500')),
            10: Decimal('5000') if picks_count == 10 else Decimal('1000'),
        }
        self.payout_table = {k: float(v) for k, v in payouts.items()}

    def play_game(self):
        """Lance le jeu Keno"""
        self.generate_payouts()
        
        # Tire 20 numéros sur 80
        all_numbers = list(range(1, 81))
        self.drawn_numbers = sorted(random.sample(all_numbers, 20))
        
        # Compte les correspondances
        matches = sum(1 for pick in self.picks if pick in self.drawn_numbers)
        self.matches = matches
        
        # Calcule les gains
        payouts = self.payout_table
        if matches in payouts:
            multiplier = Decimal(str(payouts[matches]))
            self.winnings = self.bet_amount * multiplier
            self.result = 'win' if multiplier > 0 else 'lose'
        else:
            self.winnings = Decimal('0')
            self.result = 'lose'
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()