from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class Spanish21Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='spanish_21_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50.00'))
    player_cards = models.JSONField(default=list)
    dealer_cards = models.JSONField(default=list)
    
    player_score = models.IntegerField(default=0)
    dealer_score = models.IntegerField(default=0)
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    result = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, default='finished')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Spanish 21 Game {self.id} - {self.player.username}"

    def calculate_score(self, cards):
        """Calcule le score des cartes (règles Spanish 21)"""
        score = 0
        aces = 0
        
        for card in cards:
            rank = card % 13
            if rank == 0:  # As
                aces += 1
                score += 11
            elif rank >= 9:  # Figures (10, V, D, R)
                score += 10
            else:
                score += rank + 1
        
        # Ajuster les As
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
        
        return score

    def play_game(self):
        """Lance le jeu Spanish 21"""
        # Deck Spanish 21 (sans les 10)
        deck = []
        for suit in range(4):  # 4 couleurs
            for rank in range(13):  # 13 rangs
                if rank < 9:  # Exclure les 10 (ranks 9-12)
                    deck.append(suit * 13 + rank + 1)
        
        random.shuffle(deck)
        
        # Distribution
        self.player_cards = [deck.pop(), deck.pop()]
        self.dealer_cards = [deck.pop(), deck.pop()]
        
        self.player_score = self.calculate_score(self.player_cards)
        self.dealer_score = self.calculate_score(self.dealer_cards)
        
        # Vérifier Spanish 21 (6 cartes = 21)
        if len(self.player_cards) >= 6 and self.player_score == 21:
            self.winnings = self.bet_amount * Decimal('3')  # 6-card 21 = 3x
            self.result = 'spanish_21'
        elif self.player_score > 21:
            self.result = 'lose'
        elif self.dealer_score > 21:
            self.winnings = self.bet_amount * Decimal('2')
            self.result = 'win'
        elif self.player_score > self.dealer_score:
            self.winnings = self.bet_amount * Decimal('2')
            self.result = 'win'
        elif self.player_score < self.dealer_score:
            self.result = 'lose'
        else:
            self.winnings = self.bet_amount  # Égalité = remboursement
            self.result = 'push'
        
        if self.result not in ['win', 'spanish_21', 'push']:
            self.winnings = Decimal('0')
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()