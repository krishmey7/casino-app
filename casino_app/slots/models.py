from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random


class SlotsGame(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'En attente'),
        ('spinning', 'En cours de rotation'),
        ('won', 'Gagné'),
        ('lost', 'Perdu'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='slots_games')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    
    # Symboles (3 rouleaux, 5 symboles possibles: cherry, bar, diamond, seven, jackpot)
    # Valeurs: 0=cerise, 1=bar, 2=diamant, 3=sept, 4=jackpot
    reel_1 = models.IntegerField(default=0)  # Tambour 1
    reel_2 = models.IntegerField(default=0)  # Tambour 2
    reel_3 = models.IntegerField(default=0)  # Tambour 3
    
    # Pari et gains
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    multiplier = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    
    # Combinaisons gagnantes
    SYMBOL_NAMES = {
        0: 'cerise',
        1: 'bar',
        2: 'diamant',
        3: 'sept',
        4: 'jackpot'
    }
    
    # Table de paiement
    PAYOUTS = {
        'jackpot_jackpot_jackpot': Decimal('500.00'),  # 4-4-4 = 500x
        'sept_sept_sept': Decimal('100.00'),  # 3-3-3 = 100x
        'diamant_diamant_diamant': Decimal('50.00'),  # 2-2-2 = 50x
        'bar_bar_bar': Decimal('25.00'),  # 1-1-1 = 25x
        'cerise_cerise_cerise': Decimal('10.00'),  # 0-0-0 = 10x
        'cerise_any_any': Decimal('2.00'),  # Cerise x1 = 2x
    }
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Slots Game {self.id} - {self.player.username} - {self.status}"

    def spin(self):
        """Effectue une rotation des tambours"""
        if self.status != 'waiting':
            return {'error': 'Game already spinning or finished'}
        
        self.status = 'spinning'
        # Générer 3 symboles aléatoires (0-4)
        self.reel_1 = random.randint(0, 4)
        self.reel_2 = random.randint(0, 4)
        self.reel_3 = random.randint(0, 4)
        
        # Calculer les gains basés sur les symboles
        self.multiplier = self._calculate_payout()
        
        if self.multiplier > Decimal('1.00'):
            self.status = 'won'
            self.winnings = self.bet_amount * self.multiplier
        else:
            self.status = 'lost'
            self.winnings = Decimal('0.00')
        
        self.ended_at = timezone.now()
        self.save()
        
        return {
            'reel_1': self.reel_1,
            'reel_2': self.reel_2,
            'reel_3': self.reel_3,
            'multiplier': float(self.multiplier),
            'winnings': float(self.winnings),
            'status': self.status
        }

    def _calculate_payout(self):
        """Calcule le multiplicateur basé sur les symboles"""
        symbols = [self.reel_1, self.reel_2, self.reel_3]
        symbol_names = [self.SYMBOL_NAMES[s] for s in symbols]
        
        # Vérifier jackpot (4-4-4)
        if all(s == 4 for s in symbols):
            return self.PAYOUTS['jackpot_jackpot_jackpot']
        
        # Vérifier sept (3-3-3)
        if all(s == 3 for s in symbols):
            return self.PAYOUTS['sept_sept_sept']
        
        # Vérifier diamant (2-2-2)
        if all(s == 2 for s in symbols):
            return self.PAYOUTS['diamant_diamant_diamant']
        
        # Vérifier bar (1-1-1)
        if all(s == 1 for s in symbols):
            return self.PAYOUTS['bar_bar_bar']
        
        # Vérifier cerise (0-0-0)
        if all(s == 0 for s in symbols):
            return self.PAYOUTS['cerise_cerise_cerise']
        
        # Vérifier cerise simple (au moins une cerise)
        if 0 in symbols:
            return self.PAYOUTS['cerise_any_any']
        
        return Decimal('1.00')  # Pas de gain
