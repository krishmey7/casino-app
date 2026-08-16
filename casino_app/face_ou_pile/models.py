from django.db import models
from django.conf import settings
from decimal import Decimal
import secrets


class FaceOuPileGame(models.Model):
    CHOICES = [
        ('face', 'Face'),
        ('pile', 'Pile'),
    ]
    STATUS_CHOICES = [
        ('waiting', 'En attente'),
        ('playing', 'En cours'),
        ('finished', 'Terminé'),
    ]

    player1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fop_games_as_player1')
    player2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fop_games_as_player2', null=True, blank=True)
    bet_amount = models.DecimalField(max_digits=10, decimal_places=2)
    chooser_choice = models.CharField(max_length=10, choices=CHOICES, null=True, blank=True)  # Choix du chooser de la manche actuelle
    coin_result = models.CharField(max_length=10, choices=CHOICES, null=True, blank=True)  # Résultat du tirage de la manche actuelle
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='fop_wins')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    # BO3 fields
    player1_score = models.IntegerField(default=0)  # Score du joueur 1 (max 2)
    player2_score = models.IntegerField(default=0)  # Score du joueur 2 (max 2)
    current_round = models.IntegerField(default=1)  # Manche actuelle (1-3)
    round_chooser = models.CharField(max_length=10, null=True, blank=True)  # 'player1' ou 'player2' - qui choisit pour la manche actuelle
    round_results = models.JSONField(default=list, blank=True)  # Historique des manches [{'round': 1, 'chooser': 'player1', 'result': 'face', 'winner': 'player1'}]

    def __str__(self):
        return f"Jeu {self.id} : {self.player1} vs {self.player2 or 'En attente'}"

    def get_opponent_choice(self, chooser_choice):
        """Retourne le côté opposé du choix donné"""
        if not chooser_choice:
            return None
        return 'pile' if chooser_choice == 'face' else 'face'

    def determine_round_winner(self):
        """Détermine le gagnant de la manche actuelle basé sur le résultat du tirage"""
        if not self.coin_result or not self.round_chooser or not self.chooser_choice:
            return None
        
        # Normalisation stricte pour éviter tout rejet dû à la casse ou aux espaces
        chosen = str(self.chooser_choice).lower().strip()
        actual = str(self.coin_result).lower().strip()
        
        # Si le chooser a vu juste -> Il gagne. Sinon -> L'adversaire gagne.
        if chosen == actual:
            return self.player1 if self.round_chooser == 'player1' else self.player2
        else:
            return self.player2 if self.round_chooser == 'player1' else self.player1

    def determine_game_winner(self):
        """Détermine le gagnant du BO3 (premier à 2)"""
        if self.player1_score >= 2:
            return self.player1
        elif self.player2_score >= 2:
            return self.player2
        return None

    def flip_coin(self):
        """Effectue le tirage aléatoire 50/50 avec secrets pour impartialité cryptographique"""
        self.coin_result = secrets.choice(['face', 'pile'])
        return self.coin_result

    def setup_round(self):
        """Configure la manche actuelle (détermine qui choisit)"""
        if self.current_round == 1:
            self.round_chooser = 'player1'
        elif self.current_round == 2:
            self.round_chooser = 'player2'
        elif self.current_round == 3:
            # Tirage aléatoire pour la manche décisive
            self.round_chooser = random.choice(['player1', 'player2'])
        
        # Reset du choix et résultat pour la nouvelle manche
        self.chooser_choice = None
        self.coin_result = None

    def complete_round(self):
        """Termine la manche actuelle et met à jour les scores"""
        round_winner = self.determine_round_winner()
        if round_winner:
            if round_winner == self.player1:
                self.player1_score += 1
            else:
                self.player2_score += 1
            
            # Enregistrer le résultat de la manche
            self.round_results.append({
                'round': self.current_round,
                'chooser': self.round_chooser,
                'result': self.coin_result,
                'winner': 'player1' if round_winner == self.player1 else 'player2'
            })
            
            # Vérifier si la partie est terminée
            if self.player1_score >= 2 or self.player2_score >= 2:
                self.winner = self.determine_game_winner()
                self.status = 'finished'
                from django.utils import timezone
                self.finished_at = timezone.now()
            else:
                # Passer à la manche suivante
                self.current_round += 1
                self.setup_round()

    def payout(self):
        from casino_app.wallet.models import Wallet

        total_pot = self.bet_amount * Decimal('2')
        # 95% du pot au gagnant (5% commission)
        winnings = total_pot * Decimal('0.95')
        
        if not self.winner:
            return

        winner_wallet = Wallet.objects.get(utilisateur=self.winner)
        winner_wallet.credit(winnings, f'Gagné au Face ou Pile BO3 contre {self.player2 if self.winner == self.player1 else self.player1}')
