from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid
import random

class BaccaratGame(models.Model):
    RESULT_CHOICES = [
        ('player', 'Joueur'),
        ('banker', 'Banquier'),
        ('tie', 'Égalité'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='baccarat_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    bet_on = models.CharField(max_length=10, choices=RESULT_CHOICES, default='player')
    
    player_hand = models.JSONField(default=list)
    banker_hand = models.JSONField(default=list)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, null=True, blank=True)
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    status = models.CharField(max_length=10, default='playing')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Baccarat Game {self.id} - {self.player.username}"

    def deal_game(self):
        """Distribue les cartes et joue la partie"""
        deck = [i % 13 + 1 for i in range(52)]
        random.shuffle(deck)
        
        self.player_hand = [deck[0], deck[2]]
        self.banker_hand = [deck[1], deck[3]]
        self.evaluate_game()

    def evaluate_game(self):
        """Évalue la main et détermine le gagnant"""
        from django.utils import timezone
        
        player_value = self.hand_value(self.player_hand)
        banker_value = self.hand_value(self.banker_hand)
        
        if player_value > banker_value:
            self.result = 'player'
        elif banker_value > player_value:
            self.result = 'banker'
        else:
            self.result = 'tie'
        
        # Calculer les gains
        if self.result == self.bet_on:
            if self.result == 'tie':
                self.winnings = self.bet_amount * 8
            elif self.result == 'banker':
                self.winnings = self.bet_amount * 0.95
            else:
                self.winnings = self.bet_amount
        else:
            self.winnings = Decimal('0.00')
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()

    def hand_value(self, hand):
        """Calcule la valeur d'une main au Baccarat"""
        value = sum(hand)
        return value % 10