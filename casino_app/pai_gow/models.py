from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class PaiGowGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pai_gow_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    
    # Tiles: valeurs 0-9 (nous utilisons des tuiles simplifiées)
    player_tiles = models.JSONField(default=list)  # 2 tiles pour le joueur
    banker_tiles = models.JSONField(default=list)  # 2 tiles pour le banquier
    
    # High hand et Low hand
    player_high = models.IntegerField(default=0)
    player_low = models.IntegerField(default=0)
    banker_high = models.IntegerField(default=0)
    banker_low = models.IntegerField(default=0)
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    result = models.CharField(max_length=10, null=True, blank=True)  # win/lose/tie
    status = models.CharField(max_length=10, default='finished')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Pai Gow Game {self.id} - {self.player.username}"

    def deal_game(self):
        """Distribue les tuiles et joue la partie"""
        # Tire 4 tuiles (0-9 pour simplification)
        tiles = random.sample(range(1, 11), 4)  # 1-10
        
        self.player_tiles = tiles[:2]
        self.banker_tiles = tiles[2:]
        
        # Arrange les mains automatiquement (simple arrangement)
        self.arrange_hands()
        self.determine_winner()

    def arrange_hands(self):
        """Arrange les tuiles en high et low hand"""
        # Pour le joueur: arrange pour maximiser les gains
        p1, p2 = self.player_tiles
        if p1 > p2:
            self.player_high = p1
            self.player_low = p2
        else:
            self.player_high = p2
            self.player_low = p1
        
        # Pour le banquier: arrange aléatoirement
        b1, b2 = self.banker_tiles
        if random.random() > 0.5:
            self.banker_high = b1
            self.banker_low = b2
        else:
            self.banker_high = b2
            self.banker_low = b1

    def determine_winner(self):
        """Détermine le gagnant"""
        player_high_win = self.player_high > self.banker_high
        player_low_win = self.player_low > self.banker_low
        
        # Compte les mains gagnées
        wins = int(player_high_win) + int(player_low_win)
        
        if wins == 2:
            self.result = 'win'
            self.winnings = self.bet_amount * Decimal('1.95')  # Moins 5% de commission
        elif wins == 1:
            self.result = 'tie'
            self.winnings = self.bet_amount  # Retour de la mise
        else:
            self.result = 'lose'
            self.winnings = Decimal('0')
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()