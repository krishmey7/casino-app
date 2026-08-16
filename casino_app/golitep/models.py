from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random
import json


class MinesGame(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Facile (1 mine)'),
        ('medium', 'Moyen (12 mines)'),
        ('hard', 'Difficile (24 mines)'),
        ('custom', 'Personnalisé'),
    ]
    
    STATUS_CHOICES = [
        ('waiting', 'En attente'),
        ('playing', 'En cours'),
        ('won', 'Gagné'),
        ('lost', 'Perdu'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mines_games')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='playing')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    
    # Grille (5x5 = 25 cases)
    grid = models.JSONField(default=list)  # Positions des mines [0-24]
    revealed = models.JSONField(default=list)  # Cases révélées [0-24]
    
    # Pari et gains
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    current_multiplier = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    
    # Statistiques
    cells_revealed = models.IntegerField(default=0)  # Nombre de cases révélées
    mines_count = models.IntegerField(default=12)
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Mines Game {self.id} - {self.player.username} - {self.status}"

    def initialize_game(self, mines_count=12):
        """Initialise une nouvelle partie avec les mines"""
        self.mines_count = mines_count
        self.grid = random.sample(range(25), mines_count)  # Positions aléatoires des mines
        self.revealed = []
        self.cells_revealed = 0
        self.current_multiplier = Decimal('1.00')
        self.status = 'playing'
        self.save()

    def reveal_cell(self, cell_number):
        """Révèle une case"""
        if cell_number in self.revealed:
            return {'error': 'Cell already revealed'}
        
        self.revealed.append(cell_number)
        
        if cell_number in self.grid:
            # MINE - Partie perdue
            self.status = 'lost'
            self.ended_at = timezone.now()
            self.winnings = Decimal('0.00')
            self.save()
            return {'hit_mine': True, 'lost': True}
        else:
            # Safe - Continuer
            self.cells_revealed += 1
            # Multiplicateur augmente à chaque case révélée
            # Formule : 1.00 + (0.01 * cells_revealed)
            self.current_multiplier = Decimal(str(round(1.0 + (0.02 * self.cells_revealed), 2)))
            self.save()
            return {'hit_mine': False, 'multiplier': float(self.current_multiplier)}

    def cash_out(self):
        """Encaisser les gains"""
        if self.status != 'playing':
            return {'error': 'Game not playing'}
        
        self.status = 'won'
        self.winnings = self.bet_amount * self.current_multiplier
        self.ended_at = timezone.now()
        self.save()
        return {'winnings': float(self.winnings), 'multiplier': float(self.current_multiplier)}
