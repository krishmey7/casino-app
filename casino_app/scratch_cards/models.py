from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class ScratchCardGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scratch_card_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50.00'))
    card_type = models.CharField(max_length=20, default='classic')  # classic, deluxe, premium
    
    symbols = models.JSONField(default=list)  # Liste des symboles grattés
    prize = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    result = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, default='finished')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Scratch Card Game {self.id} - {self.player.username}"

    def get_card_config(self):
        """Configuration des cartes selon le type"""
        configs = {
            'classic': {
                'symbols': ['🍒', '🍋', '🍊', '⭐', '💎', '7️⃣', '💰'],
                'prizes': {
                    '🍒🍒🍒': 2,
                    '🍋🍋🍋': 3,
                    '🍊🍊🍊': 4,
                    '⭐⭐⭐': 5,
                    '💎💎💎': 10,
                    '7️⃣7️⃣7️⃣': 20,
                    '💰💰💰': 50
                }
            },
            'deluxe': {
                'symbols': ['🍒', '🍋', '🍊', '⭐', '💎', '7️⃣', '💰', '🎰', '👑'],
                'prizes': {
                    '🍒🍒🍒': 3,
                    '🍋🍋🍋': 5,
                    '🍊🍊🍊': 7,
                    '⭐⭐⭐': 10,
                    '💎💎💎': 20,
                    '7️⃣7️⃣7️⃣': 50,
                    '💰💰💰': 100,
                    '🎰🎰🎰': 200,
                    '👑👑👑': 500
                }
            },
            'premium': {
                'symbols': ['🍒', '🍋', '🍊', '⭐', '💎', '7️⃣', '💰', '🎰', '👑', '💎', '🏆'],
                'prizes': {
                    '🍒🍒🍒': 5,
                    '🍋🍋🍋': 10,
                    '🍊🍊🍊': 15,
                    '⭐⭐⭐': 25,
                    '💎💎💎': 50,
                    '7️⃣7️⃣7️⃣': 100,
                    '💰💰💰': 250,
                    '🎰🎰🎰': 500,
                    '👑👑👑': 1000,
                    '🏆🏆🏆': 2500
                }
            }
        }
        return configs.get(self.card_type, configs['classic'])

    def generate_symbols(self):
        """Génère les symboles de la carte"""
        config = self.get_card_config()
        symbols = config['symbols']
        
        # Génère 9 symboles (3x3 grille)
        self.symbols = [random.choice(symbols) for _ in range(9)]
        
        # Vérifie les combinaisons gagnantes
        self.prize = self.calculate_prize()

    def calculate_prize(self):
        """Calcule le prix gagné"""
        config = self.get_card_config()
        prizes = config['prizes']
        
        # Vérifie les lignes horizontales
        for i in range(0, 9, 3):
            line = ''.join(self.symbols[i:i+3])
            if line in prizes:
                return Decimal(str(prizes[line]))
        
        # Vérifie les lignes verticales
        for i in range(3):
            line = self.symbols[i] + self.symbols[i+3] + self.symbols[i+6]
            if line in prizes:
                return Decimal(str(prizes[line]))
        
        # Vérifie les diagonales
        diagonal1 = self.symbols[0] + self.symbols[4] + self.symbols[8]
        diagonal2 = self.symbols[2] + self.symbols[4] + self.symbols[6]
        
        if diagonal1 in prizes:
            return Decimal(str(prizes[diagonal1]))
        if diagonal2 in prizes:
            return Decimal(str(prizes[diagonal2]))
        
        return Decimal('0.00')

    def play_game(self):
        """Lance le jeu Scratch Cards"""
        self.generate_symbols()
        
        if self.prize > 0:
            self.winnings = self.prize
            self.result = 'win'
        else:
            self.result = 'lose'
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()