from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random


class LuckyNumberGame(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'En attente'),
        ('playing', 'En cours'),
        ('finished', 'Fini'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    winning_number = models.IntegerField(null=True, blank=True)  # Numéro gagnant (0-9)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Lucky Number Game {self.id} - {self.status}"

    def start_game(self):
        """Démarre une partie"""
        self.status = 'playing'
        self.save()

    def finish_game(self):
        """Termine une partie et génère le chiffre gagnant"""
        self.status = 'finished'
        self.winning_number = random.randint(0, 9)  # Tirage aléatoire entre 0 et 9
        self.finished_at = timezone.now()
        self.save()


class LuckyNumberBet(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('won', 'Gagné'),
        ('lost', 'Perdu'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(LuckyNumberGame, on_delete=models.CASCADE, related_name='bets')
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lucky_number_bets')
    chosen_number = models.IntegerField()  # Chiffre choisi par le joueur (0-9)
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    bet_time = models.DateTimeField(auto_now_add=True)
    result_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Bet {self.id} - {self.player.username} - {self.status}"

    def check_result(self):
        """Vérifie si le pari est gagnant"""
        if self.game.winning_number is None:
            return
        
        if self.chosen_number == self.game.winning_number:
            self.status = 'won'
            self.winnings = self.bet_amount * Decimal('10')  # Gain de 10x
        else:
            self.status = 'lost'
            self.winnings = Decimal('0.00')
        
        self.result_time = timezone.now()
        self.save()
        return self.status == 'won'
