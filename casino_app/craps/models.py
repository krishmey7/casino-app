from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class CrapsGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='craps_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    bet_type = models.CharField(max_length=20, default='pass')  # pass, dont_pass, come, dont_come
    
    dice_roll = models.JSONField(default=list)  # [die1, die2]
    point = models.IntegerField(default=0)
    result = models.CharField(max_length=10, choices=[('win', 'Gagné'), ('lose', 'Perdu')], null=True, blank=True)
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    status = models.CharField(max_length=10, default='playing')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Craps Game {self.id} - {self.player.username}"

    def roll_dice(self):
        """Lance les dés"""
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        self.dice_roll = [die1, die2]
        total = die1 + die2
        
        if self.point == 0:  # Come out roll
            if total in [7, 11]:
                self.result = 'win' if self.bet_type == 'pass' else 'lose'
                self.winnings = self.bet_amount
                self.status = 'finished'
            elif total in [2, 3, 12]:
                self.result = 'lose' if self.bet_type == 'pass' else 'win'
                self.winnings = self.bet_amount if self.result == 'win' else Decimal('0')
                self.status = 'finished'
            else:
                self.point = total
                self.status = 'point_established'
        else:  # Point already established
            if total == self.point:
                self.result = 'win' if self.bet_type == 'pass' else 'lose'
                self.winnings = self.bet_amount
                self.status = 'finished'
            elif total == 7:
                self.result = 'lose' if self.bet_type == 'pass' else 'win'
                self.winnings = self.bet_amount if self.result == 'win' else Decimal('0')
                self.status = 'finished'
        
        if self.status == 'finished':
            self.ended_at = timezone.now()
        
        self.save()