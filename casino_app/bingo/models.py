from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class BingoGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bingo_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    card = models.JSONField(default=list)  # Grille 5x5
    drawn_numbers = models.JSONField(default=list)  # Numéros tirés
    
    lines_complete = models.IntegerField(default=0)  # Lignes complètes
    column_complete = models.IntegerField(default=0)  # Colonnes complètes
    full_card = models.BooleanField(default=False)  # Carte complète
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    result = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, default='playing')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Bingo Game {self.id} - {self.player.username}"

    def generate_card(self):
        """Génère une grille Bingo 5x5"""
        ranges = [
            list(range(1, 16)),      # B: 1-15
            list(range(16, 31)),     # I: 16-30
            list(range(31, 46)),     # N: 31-45
            list(range(46, 61)),     # G: 46-60
            list(range(61, 76)),     # O: 61-75
        ]
        card = []
        for col in range(5):
            column = []
            for row in range(5):
                if col == 2 and row == 2:
                    column.append(0)  # Centre = Joker
                else:
                    column.append(random.choice(ranges[col]))
            card.append(column)
        self.card = card

    def draw_number(self):
        """Tire un nouveau numéro"""
        used = set(self.drawn_numbers)
        available = [n for n in range(1, 76) if n not in used]
        if available:
            num = random.choice(available)
            self.drawn_numbers.append(num)
            return num
        return None

    def check_win(self):
        """Vérifie les gains"""
        drawn_set = set(self.drawn_numbers)
        
        # Vérifie lignes
        lines = 0
        for row in range(5):
            if all(self.card[col][row] == 0 or self.card[col][row] in drawn_set for col in range(5)):
                lines += 1
        
        # Vérifie colonnes
        columns = 0
        for col in range(5):
            if all(self.card[col][row] == 0 or self.card[col][row] in drawn_set for row in range(5)):
                columns += 1
        
        # Vérifie carte complète
        full = all(self.card[col][row] == 0 or self.card[col][row] in drawn_set 
                   for col in range(5) for row in range(5))
        
        self.lines_complete = lines
        self.column_complete = columns
        self.full_card = full
        
        if full:
            self.winnings = self.bet_amount * 50
            self.result = 'win5'
            self.status = 'finished'
        elif lines >= 2 or columns >= 2:
            self.winnings = self.bet_amount * 10
            self.result = 'win2'
            self.status = 'finished'
        elif lines >= 1 or columns >= 1:
            self.winnings = self.bet_amount * 3
            self.result = 'win1'
            self.status = 'finished'