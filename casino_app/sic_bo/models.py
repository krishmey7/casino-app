from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class SicBoGame(models.Model):
    OUTCOME_CHOICES = [(choice, choice) for choice in [
        'small', 'big', 'odd', 'even', 'triple', 'pair',
        'single_1', 'single_2', 'single_3', 'single_4', 'single_5', 'single_6',
        'total_4', 'total_5', 'total_6', 'total_7', 'total_8', 'total_9',
        'total_10', 'total_11', 'total_12', 'total_13', 'total_14', 'total_15',
        'total_16', 'total_17'
    ]]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sic_bo_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    bet_type = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default='small')
    
    dice = models.JSONField(default=list)  # 3 dés
    total = models.IntegerField(default=0)
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    result = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, default='finished')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Sic Bo Game {self.id} - {self.player.username}"

    def roll_dice(self):
        """Lance les 3 dés"""
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        die3 = random.randint(1, 6)
        self.dice = [die1, die2, die3]
        self.total = die1 + die2 + die3
        
        # Détermine le résultat
        is_winning = self.check_win()
        self.result = 'win' if is_winning else 'lose'
        
        if is_winning:
            self.winnings = self.calculate_payout()
        else:
            self.winnings = Decimal('0')
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()

    def check_win(self):
        """Vérifie si on a gagné"""
        d1, d2, d3 = self.dice
        s = self.total
        bet = self.bet_type
        
        if bet == 'small':
            return 4 <= s <= 10 and not (d1 == d2 == d3)
        elif bet == 'big':
            return 11 <= s <= 17 and not (d1 == d2 == d3)
        elif bet == 'odd':
            return s % 2 == 1 and not (d1 == d2 == d3)
        elif bet == 'even':
            return s % 2 == 0 and not (d1 == d2 == d3)
        elif bet == 'triple':
            return d1 == d2 == d3
        elif bet == 'pair':
            return d1 == d2 or d2 == d3 or d1 == d3
        elif bet.startswith('single_'):
            num = int(bet.split('_')[1])
            return self.dice.count(num) > 0
        elif bet.startswith('total_'):
            return s == int(bet.split('_')[1])
        return False

    def calculate_payout(self):
        """Calcule les gains basés sur le type de pari"""
        bet = self.bet_type
        
        payouts = {
            'small': Decimal('1'),
            'big': Decimal('1'),
            'odd': Decimal('1'),
            'even': Decimal('1'),
            'triple': Decimal('30'),
            'pair': Decimal('6'),
            'single_1': Decimal('1'),
            'single_2': Decimal('1'),
            'single_3': Decimal('1'),
            'single_4': Decimal('1'),
            'single_5': Decimal('1'),
            'single_6': Decimal('1'),
            'total_4': Decimal('50'),
            'total_5': Decimal('18'),
            'total_6': Decimal('14'),
            'total_7': Decimal('12'),
            'total_8': Decimal('8'),
            'total_9': Decimal('6'),
            'total_10': Decimal('6'),
            'total_11': Decimal('6'),
            'total_12': Decimal('6'),
            'total_13': Decimal('8'),
            'total_14': Decimal('12'),
            'total_15': Decimal('14'),
            'total_16': Decimal('18'),
            'total_17': Decimal('50'),
        }
        
        multiplier = payouts.get(bet, Decimal('1'))
        return self.bet_amount * multiplier