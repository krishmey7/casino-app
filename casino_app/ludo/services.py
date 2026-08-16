"""
Services métier pour LUDO
Gestion des transactions wallet, escrow, et logique de partie
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from typing import Optional, Dict, List
from .models import LudoGame, LudoPlayer, LudoGameTransaction
from .engine import LudoEngine


class WalletService:
    """Service pour gérer les transactions wallet"""
    
    @staticmethod
    @transaction.atomic
    def create_stake_transaction(game: LudoGame, user, amount: Decimal) -> LudoGameTransaction:
        """
        Crée une transaction de mise (escrow)
        Bloque les fonds du joueur
        """
        from casino_app.wallet.models import Wallet
        
        # Récupérer le wallet du joueur
        wallet = Wallet.objects.get(utilisateur=user)
        
        # Utiliser la méthode debit() existante du wallet
        try:
            wallet.debit(amount, f"Mise pour partie LUDO {game.id}")
        except ValueError as e:
            raise ValueError(str(e))
        
        # Créer une transaction LUDO
        ludo_transaction = LudoGameTransaction.objects.create(
            game=game,
            user=user,
            transaction_type='stake',
            amount=amount
        )
        
        return ludo_transaction
    
    @staticmethod
    @transaction.atomic
    def refund_stake(game: LudoGame, user) -> LudoGameTransaction:
        """
        Rembourse la mise à un joueur (annulation ou abandon)
        """
        from casino_app.wallet.models import Wallet
        
        # Récupérer la transaction de mise originale
        stake_transaction = LudoGameTransaction.objects.filter(
            game=game,
            user=user,
            transaction_type='stake'
        ).first()
        
        if not stake_transaction:
            raise ValueError("Aucune transaction de mise trouvée")
        
        # Récupérer le wallet du joueur
        wallet = Wallet.objects.get(utilisateur=user)
        
        # Rembourser le montant en utilisant la méthode credit()
        wallet.credit(stake_transaction.amount, f"Remboursement mise LUDO {game.id}")
        
        # Créer une transaction LUDO
        ludo_transaction = LudoGameTransaction.objects.create(
            game=game,
            user=user,
            transaction_type='refund',
            amount=stake_transaction.amount
        )
        
        return ludo_transaction
    
    @staticmethod
    @transaction.atomic
    def pay_winner(game: LudoGame, winner_user, total_pot: Decimal) -> LudoGameTransaction:
        """
        Paiement du gagnant
        Le gagnant reçoit le pot total moins les frais du casino
        """
        from casino_app.wallet.models import Wallet
        
        # Calculer le gain (pot total - frais casino)
        casino_fee = total_pot * Decimal('0.05')  # 5% de frais
        winner_amount = total_pot - casino_fee
        
        # Récupérer le wallet du gagnant
        wallet = Wallet.objects.get(utilisateur=winner_user)
        
        # Ajouter le gain au solde en utilisant la méthode credit()
        wallet.credit(winner_amount, f"Gain partie LUDO {game.id}")
        
        # Créer une transaction LUDO
        ludo_transaction = LudoGameTransaction.objects.create(
            game=game,
            user=winner_user,
            transaction_type='win',
            amount=winner_amount
        )
        
        return ludo_transaction


class GameService:
    """Service pour gérer la logique des parties"""
    
    @staticmethod
    @transaction.atomic
    def create_game(user, stake: Decimal, min_players: int = 2) -> LudoGame:
        """
        Crée une nouvelle partie
        - Crée l'instance LudoGame
        - Ajoute le créateur comme premier joueur
        - Effectue la transaction de mise (escrow)
        """
        from casino_app.wallet.models import Wallet
        
        # Créer la partie avec min_players
        game = LudoGame.objects.create(stake=stake, min_players=min_players)
        game.initialize_game_state()
        
        # Assigner une couleur au créateur (rouge par défaut)
        creator_color = 'red'
        game.add_player_to_state(creator_color)
        
        # Créer le joueur
        player = LudoPlayer.objects.create(
            game=game,
            user=user,
            color=creator_color,
            turn_order=0
        )
        
        # Effectuer la transaction de mise
        WalletService.create_stake_transaction(game, user, stake)
        
        return game
    
    @staticmethod
    @transaction.atomic
    def join_game(game: LudoGame, user) -> LudoPlayer:
        """
        Ajoute un joueur à une partie existante
        """
        # Vérifier que la partie est en attente
        if game.status != 'waiting':
            raise ValueError("La partie n'est plus en attente")
        
        # Vérifier que le joueur n'est pas déjà dans la partie
        if LudoPlayer.objects.filter(game=game, user=user).exists():
            raise ValueError("Vous êtes déjà dans cette partie")
        
        # Vérifier le nombre maximum de joueurs
        player_count = game.get_player_count()
        if player_count >= 4:
            raise ValueError("La partie est complète")
        
        # Assigner une couleur
        colors = ['red', 'blue', 'green', 'yellow']
        used_colors = [player.color for player in game.ludoplayers.all()]
        available_colors = [c for c in colors if c not in used_colors]
        
        if not available_colors:
            raise ValueError("Plus de couleurs disponibles")
        
        color = available_colors[0]
        turn_order = player_count
        
        # Créer le joueur
        player = LudoPlayer.objects.create(
            game=game,
            user=user,
            color=color,
            turn_order=turn_order
        )
        
        # Ajouter le joueur à l'état du jeu
        game.add_player_to_state(color)
        game.save()
        
        # Bloquer la mise du joueur
        WalletService.create_stake_transaction(game, user, game.stake)
        
        return player
    
    @staticmethod
    @transaction.atomic
    def start_game(game: LudoGame) -> None:
        """
        Démarre une partie (tous les joueurs sont prêts)
        """
        if not game.can_start():
            raise ValueError("Impossible de démarrer la partie")
        
        game.start_game()
        
        # Marquer tous les joueurs comme connectés
        for player in game.ludoplayers.all():
            player.mark_connected()
    
    @staticmethod
    @transaction.atomic
    def cancel_game(game: LudoGame, cancelled_by) -> None:
        """
        Annule une partie et rembourse tous les joueurs
        """
        if game.status not in ['waiting', 'active']:
            raise ValueError("Impossible d'annuler cette partie")
        
        game.status = 'cancelled'
        game.save()
        
        # Rembourser tous les joueurs
        for player in game.ludoplayers.all():
            WalletService.refund_stake(game, player.user)
    
    @staticmethod
    @transaction.atomic
    def handle_forfeit(game: LudoGame, forfeiting_user) -> None:
        """
        Gère l'abandon d'un joueur
        """
        if game.status != 'active':
            raise ValueError("La partie n'est pas active")
        
        # Marquer le joueur comme déconnecté
        player = LudoPlayer.objects.filter(game=game, user=forfeiting_user).first()
        if player:
            player.mark_disconnected()
        
        # Si c'est le dernier joueur connecté, annuler la partie
        connected_players = game.ludoplayers.filter(is_connected=True).count()
        if connected_players == 0:
            GameService.cancel_game(game, forfeiting_user)
        else:
            # Déclarer le dernier joueur connecté comme gagnant
            last_connected = game.ludoplayers.filter(is_connected=True).first()
            if last_connected:
                GameService.finish_game(game, last_connected.user)
    
    @staticmethod
    @transaction.atomic
    def finish_game(game: LudoGame, winner_user) -> None:
        """
        Termine une partie et paie le gagnant
        """
        if game.status != 'active':
            raise ValueError("La partie n'est pas active")
        
        # Calculer le pot total
        total_pot = game.stake * game.get_player_count()
        
        # Payer le gagnant
        WalletService.pay_winner(game, winner_user, total_pot)
        
        # Marquer la partie comme terminée
        game.finish_game(winner_user)
        
        # Rembourser les autres joueurs (optionnel selon les règles)
        # Ici, seul le gagnant est payé
        for player in game.ludoplayers.all():
            if player.user != winner_user:
                # Les perdants ne sont pas remboursés (mise perdue)
                pass


class TimeoutService:
    """Service pour gérer les timeouts et délais"""
    
    @staticmethod
    def check_player_timeout(player: LudoPlayer, timeout_seconds: int = 300) -> bool:
        """
        Vérifie si un joueur a dépassé le délai autorisé
        """
        if not player.is_connected:
            return True
        
        time_since_activity = (timezone.now() - player.last_activity).total_seconds()
        return time_since_activity > timeout_seconds
    
    @staticmethod
    def check_game_timeout(game: LudoGame, timeout_seconds: int = 3600) -> bool:
        """
        Vérifie si une partie a dépassé le délai autorisé
        """
        if game.status != 'active':
            return False
        
        if not game.started_at:
            return False
        
        time_since_start = (timezone.now() - game.started_at).total_seconds()
        return time_since_start > timeout_seconds
    
    @staticmethod
    def handle_inactive_players(game: LudoGame) -> List[LudoPlayer]:
        """
        Identifie les joueurs inactifs et gère leur timeout
        """
        inactive_players = []
        
        for player in game.ludoplayers.all():
            if TimeoutService.check_player_timeout(player):
                inactive_players.append(player)
                player.mark_disconnected()
        
        return inactive_players


class GameEngineService:
    """Service pour coordonner le moteur de jeu avec la base de données"""
    
    @staticmethod
    def get_game_engine(game: LudoGame) -> LudoEngine:
        """
        Crée et retourne un moteur de jeu avec l'état actuel
        """
        return LudoEngine(game.game_state)
    
    @staticmethod
    @transaction.atomic
    def save_game_state(game: LudoGame, engine: LudoEngine) -> None:
        """
        Sauvegarde l'état du jeu depuis le moteur
        """
        game.game_state = engine.get_game_state()
        game.save()
    
    @staticmethod
    @transaction.atomic
    def execute_move_and_save(game: LudoGame, color: str, token_index: int) -> Dict:
        """
        Exécute un mouvement et sauvegarde l'état
        """
        engine = GameEngineService.get_game_engine(game)
        
        result = engine.execute_move(color, token_index)
        
        if result["success"]:
            GameEngineService.save_game_state(game, engine)
            
            # Vérifier la victoire
            if engine.check_victory(color):
                player = game.ludoplayers.filter(color=color).first()
                if player:
                    GameService.finish_game(game, player.user)
                    result["victory"] = True
                    result["winner"] = player.user.username
        
        return result
    
    @staticmethod
    @transaction.atomic
    def roll_dice_and_save(game: LudoGame) -> List[int]:
        """
        Lance les dés et sauvegarde l'état
        """
        engine = GameEngineService.get_game_engine(game)
        
        dice_result = engine.roll_dice()
        GameEngineService.save_game_state(game, engine)
        
        return dice_result
    
    @staticmethod
    def get_valid_moves_for_current_turn(game: LudoGame) -> List[Dict]:
        """
        Retourne les mouvements valides pour le joueur actuel
        """
        engine = GameEngineService.get_game_engine(game)
        
        players = list(game.ludoplayers.all().order_by('turn_order'))
        current_player = players[game.current_turn]
        
        return engine.get_valid_moves_for_player(current_player.color)
    
    @staticmethod
    @transaction.atomic
    def advance_turn(game: LudoGame) -> int:
        """
        Passe au tour suivant
        """
        engine = GameEngineService.get_game_engine(game)
        
        player_count = game.get_player_count()
        new_turn = engine.next_turn(game.current_turn, player_count)
        
        game.current_turn = new_turn
        engine.reset_dice()
        GameEngineService.save_game_state(game, engine)
        
        return new_turn
