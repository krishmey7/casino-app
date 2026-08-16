from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class FanTanGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fan_tan_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    bet_type = models.CharField(max_length=1)  # 1, 2, 3, 4
    
    cards = models.JSONField(default=list)  # 4 cartes
    remainder = models.IntegerField(default=0)  # Reste de la division
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    result = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, default='finished')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Fan Tan Game {self.id} - {self.player.username}"

    def play_game(self):
        """Lance le jeu Fan Tan"""
        # Tire 4 cartes
        deck = list(range(1, 53))
        self.cards = sorted(random.sample(deck, 4))
        
        # Calcule le reste
        total = sum(self.cards)
        self.remainder = total % 4
        
        # Détermine le gagnant
        is_winning = str(self.remainder) == self.bet_type or (self.remainder == 0 and self.bet_type == '4')
        self.result = 'win' if is_winning else 'lose'
        
        if is_winning:
            self.winnings = self.bet_amount * Decimal('3')
        else:
            self.winnings = Decimal('0')
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()