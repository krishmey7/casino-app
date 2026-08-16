from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class RedDogGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='red_dog_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    bet_type = models.CharField(max_length=10, default='spread')  # spread, high, low
    
    cards = models.JSONField(default=list)  # 3 cartes
    spread = models.IntegerField(default=0)  # Écart entre les cartes
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    result = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, default='finished')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Red Dog Game {self.id} - {self.player.username}"

    def play_game(self):
        """Lance le jeu Red Dog"""
        # Tire 3 cartes
        deck = list(range(1, 53))
        self.cards = sorted(random.sample(deck, 3))
        
        # Calcule l'écart
        card1, card2, card3 = self.cards
        self.spread = abs(card2 - card1)
        
        # Détermine le résultat
        if card1 == card2 or card2 == card3:
            self.result = 'lose'  # Paires = perte
        elif self.spread == 0:
            self.result = 'lose'  # Même carte = perte
        elif self.bet_type == 'spread':
            if self.spread >= 1:
                multipliers = {1: 5, 2: 4, 3: 2, 4: 1}
                multiplier = multipliers.get(self.spread, 1)
                self.winnings = self.bet_amount * multiplier
                self.result = 'win'
            else:
                self.result = 'lose'
        elif self.bet_type == 'high':
            if card3 > card2:
                self.winnings = self.bet_amount * Decimal('1')
                self.result = 'win'
            else:
                self.result = 'lose'
        elif self.bet_type == 'low':
            if card3 < card2:
                self.winnings = self.bet_amount * Decimal('1')
                self.result = 'win'
            else:
                self.result = 'lose'
        
        if self.result != 'win':
            self.winnings = Decimal('0')
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()