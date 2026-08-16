from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import json


class Game(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'En attente'),
        ('active', 'En cours'),
        ('finished', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='checkers_games_as_player1')
    player2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='checkers_games_as_player2', null=True, blank=True)
    stake = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    
    # État du jeu
    board_state = models.JSONField(default=dict)  # Plateau de jeu sérialisé
    current_turn = models.IntegerField(default=1)  # 1 ou 2
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='checkers_wins')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_move_at = models.DateTimeField(null=True, blank=True)
    move_history = models.JSONField(default=list)  # Historique des mouvements
    
    class Meta:
        verbose_name = 'Partie de Dames'
        verbose_name_plural = 'Parties de Dames'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Game {self.id} - {self.player1.username} vs {self.player2.username if self.player2 else 'Waiting'} - {self.status}"
    
    def initialize_board(self):
        """Initialise le plateau de jeu standard (Dames internationales 10x10)"""
        board = {}
        # Plateau 10x10, cases noires seulement (positions où (row+col) % 2 == 1)
        for row in range(10):
            for col in range(10):
                if (row + col) % 2 == 1:
                    board[f"{row}{col}"] = None

        # Position initiale des pions (20 pions par joueur)
        # Joueur 1 (en bas, pions 'b' pour black) - 4 rangées
        for row in range(6, 10):
            for col in range(10):
                if (row + col) % 2 == 1:
                    board[f"{row}{col}"] = 'b'  # Pion noir

        # Joueur 2 (en haut, pions 'w' pour white) - 4 rangées
        for row in range(0, 4):
            for col in range(10):
                if (row + col) % 2 == 1:
                    board[f"{row}{col}"] = 'w'  # Pion blanc

        self.board_state = board
        self.current_turn = 1
        self.last_move_at = timezone.now()
        self.save()
    
    def is_player_turn(self, user):
        """Vérifie si c'est le tour du joueur"""
        if user == self.player1:
            return self.current_turn == 1
        elif user == self.player2:
            return self.current_turn == 2
        return False
    
    @transaction.atomic
    def lock_funds(self, user, amount):
        """Bloque les fonds pour un joueur via escrow"""
        from casino_app.wallet.models import Wallet
        
        wallet = Wallet.objects.select_for_update().get(utilisateur=user)
        if wallet.balance < amount:
            raise ValueError("Solde insuffisant")
        
        # Créer la transaction d'escrow
        GameTransaction.objects.create(
            game=self,
            user=user,
            wallet=wallet,
            amount=amount,
            status='locked',
            transaction_type='escrow'
        )
        
        # Débiter le wallet
        wallet.debit(amount, f"Mise escrow - Partie {self.id}")
        return True
    
    @transaction.atomic
    def release_funds_to_winner(self):
        """Libère les fonds au gagnant"""
        if not self.winner:
            raise ValueError("Pas de gagnant défini")

        from casino_app.wallet.models import Wallet

        # Récupérer toutes les transactions liées à ce jeu
        transactions = GameTransaction.objects.filter(game=self, status='locked')
        total_pot = sum(tx.amount for tx in transactions)

        # Libérer les transactions
        transactions.update(status='released')

        # Créditer le gagnant
        winner_wallet = Wallet.objects.get(utilisateur=self.winner)
        winner_wallet.credit(total_pot, f"Gain partie dames - Partie {self.id}")

        return total_pot
    
    @transaction.atomic
    def refund_all_funds(self):
        """Rembourse tous les joueurs en cas d'annulation"""
        from casino_app.wallet.models import Wallet

        transactions = GameTransaction.objects.filter(game=self, status='locked')

        for tx in transactions:
            # Rembourser le joueur
            wallet = Wallet.objects.get(utilisateur=tx.user)
            wallet.credit(tx.amount, f"Remboursement partie dames - Partie {self.id}")

            # Marquer la transaction comme remboursée
            tx.status = 'refunded'
            tx.save()


class GameTransaction(models.Model):
    STATUS_CHOICES = [
        ('locked', 'Bloqué'),
        ('released', 'Libéré'),
        ('refunded', 'Remboursé'),
    ]
    
    TYPE_CHOICES = [
        ('escrow', 'Escrow'),
        ('winnings', 'Gains'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    wallet = models.ForeignKey('wallet.Wallet', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='locked')
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='escrow')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Transaction de jeu'
        verbose_name_plural = 'Transactions de jeu'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Transaction {self.id} - {self.user.username} - {self.amount} - {self.status}"
