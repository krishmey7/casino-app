from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import json


class LudoGame(models.Model):
    """Modèle principal d'une partie LUDO"""
    
    STATUS_CHOICES = [
        ('waiting', 'En attente'),
        ('active', 'En cours'),
        ('finished', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]
    
    COLOR_CHOICES = [
        ('red', 'Rouge'),
        ('blue', 'Bleu'),
        ('green', 'Vert'),
        ('yellow', 'Jaune'),
    ]
    
    # Identifiant unique
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Mise de la partie
    stake = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Nombre minimum de joueurs requis (2, 3 ou 4)
    min_players = models.IntegerField(default=2, help_text="Nombre minimum de joueurs requis pour démarrer")
    
    # État de la partie
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    
    # Tour actuel (index dans la liste des joueurs)
    current_turn = models.IntegerField(default=0)
    
    # État du jeu (JSONField léger, PAS de plateau 15x15 complet)
    # Structure: {"players": {"red": {"tokens": [0, 5, 12, -1]}, ...}, "dice": [], ...}
    game_state = models.JSONField(default=dict)
    
    # Gagnant
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ludo_wins'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Partie LUDO'
        verbose_name_plural = 'Parties LUDO'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"LUDO Game {self.id} - {self.status}"
    
    def initialize_game_state(self):
        """Initialise l'état du jeu avec une structure légère"""
        self.game_state = {
            "players": {},
            "dice": [],
            "last_dice_roll": None,
            "extra_turn": False,
            "captured_this_turn": False
        }
    
    def add_player_to_state(self, color):
        """Ajoute un joueur à l'état du jeu"""
        if "players" not in self.game_state:
            self.game_state["players"] = {}
        
        # Structure légère: positions des 4 pions (-1 = base, 56+ = terminé)
        self.game_state["players"][color] = {
            "tokens": [-1, -1, -1, -1],  # 4 pions par joueur
            "finished_tokens": 0,         # Nombre de pions terminés
            "home_stretch": False         # Est dans la zone d'arrivée
        }
    
    def get_player_count(self):
        """Retourne le nombre de joueurs dans la partie"""
        return self.ludoplayers.count()
    
    def can_start(self):
        """Vérifie si la partie peut démarrer (selon min_players, tous prêts)"""
        player_count = self.get_player_count()
        if player_count < self.min_players:
            return False
        
        # Vérifier que tous les joueurs sont prêts
        all_ready = self.ludoplayers.filter(is_ready=True).count() == player_count
        return all_ready
    
    def start_game(self):
        """Démarre la partie"""
        self.status = 'active'
        self.started_at = timezone.now()
        self.current_turn = 0
        self.game_state["dice"] = []
        self.save()
    
    def finish_game(self, winner_user):
        """Termine la partie"""
        self.status = 'finished'
        self.winner = winner_user
        self.finished_at = timezone.now()
        self.save()


class LudoPlayer(models.Model):
    """Modèle représentant un joueur dans une partie LUDO"""
    
    COLOR_CHOICES = [
        ('red', 'Rouge'),
        ('blue', 'Bleu'),
        ('green', 'Vert'),
        ('yellow', 'Jaune'),
    ]
    
    # Relations
    game = models.ForeignKey(LudoGame, on_delete=models.CASCADE, related_name='ludoplayers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ludo_players')
    
    # Attributs du joueur
    color = models.CharField(max_length=10, choices=COLOR_CHOICES)
    turn_order = models.IntegerField(default=0)  # Ordre de jeu (0, 1, 2, 3)
    
    # État du joueur
    is_connected = models.BooleanField(default=True)
    is_ready = models.BooleanField(default=False)
    remaining_time = models.IntegerField(default=0)  # Temps restant en secondes
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Joueur LUDO'
        verbose_name_plural = 'Joueurs LUDO'
        ordering = ['turn_order']
        unique_together = ['game', 'user']
    
    def __str__(self):
        return f"{self.user.username} ({self.color}) - Game {self.game.id}"
    
    def update_activity(self):
        """Met à jour la dernière activité du joueur"""
        self.last_activity = timezone.now()
        self.save()
    
    def mark_ready(self):
        """Marque le joueur comme prêt"""
        self.is_ready = True
        self.save()
    
    def mark_connected(self):
        """Marque le joueur comme connecté"""
        self.is_connected = True
        self.update_activity()
    
    def mark_disconnected(self):
        """Marque le joueur comme déconnecté"""
        self.is_connected = False
        self.save()


class LudoGameTransaction(models.Model):
    """Transaction de mise pour une partie LUDO"""
    
    TRANSACTION_TYPES = [
        ('stake', 'Mise'),
        ('refund', 'Remboursement'),
        ('win', 'Gain'),
    ]
    
    game = models.ForeignKey(LudoGame, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ludo_transactions')
    
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Transaction LUDO'
        verbose_name_plural = 'Transactions LUDO'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.user.username}"
