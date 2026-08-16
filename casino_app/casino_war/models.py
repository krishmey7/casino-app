from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class CasinoWarGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='casino_war_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50.00'))
    player_card = models.IntegerField()
    dealer_card = models.IntegerField()
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    result = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, default='finished')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Casino War Game {self.id} - {self.player.username}"

    def play_game(self):
        """Lance le jeu Casino War"""
        # Tire 2 cartes
        deck = list(range(1, 53))
        cards = random.sample(deck, 2)
        self.player_card = cards[0]
        self.dealer_card = cards[1]
        
        player_rank = self.player_card % 13
        dealer_rank = self.dealer_card % 13
        
        if player_rank > dealer_rank:
            self.winnings = self.bet_amount * Decimal('2')
            self.result = 'win'
        elif player_rank < dealer_rank:
            self.result = 'lose'
        else:
            # Guerre - égalité
            # Tire 3 cartes supplémentaires pour départager
            remaining_cards = [c for c in deck if c not in cards]
            war_cards = random.sample(remaining_cards, 4)  # 2 pour chaque joueur
            
            player_war_rank = max(war_cards[0] % 13, war_cards[1] % 13)
            dealer_war_rank = max(war_cards[2] % 13, war_cards[3] % 13)
            
            if player_war_rank > dealer_war_rank:
                self.winnings = self.bet_amount * Decimal('10')  # Victoire en guerre = 10x
                self.result = 'war_win'
            else:
                self.result = 'lose'
        
        if self.result not in ['win', 'war_win']:
            self.winnings = Decimal('0')
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()