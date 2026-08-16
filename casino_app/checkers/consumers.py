import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Game


class CheckersGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'checkers_{self.game_id}'

        # Vérifier que l'utilisateur est autorisé à rejoindre
        is_authorized = await self.check_authorization()
        if not is_authorized:
            await self.close()
            return

        # Rejoindre le groupe WebSocket
        await self.channel_layer.group_add(self.game_group_name, self.channel_name)
        await self.accept()

        # Envoyer l'état initial du jeu
        await self.send_game_state()

    @database_sync_to_async
    def check_authorization(self):
        """Vérifier que l'utilisateur est un joueur de la partie"""
        try:
            game = Game.objects.select_related('player1', 'player2').get(id=self.game_id)
            return game.player1 == self.user or game.player2 == self.user
        except Game.DoesNotExist:
            return False

    async def disconnect(self, close_code):
        # Quitter le groupe WebSocket
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)

        # Si la partie est active, vérifier si l'autre joueur est toujours connecté
        game = await self.get_game()
        if game and game.status == 'active':
            # Notifier l'autre joueur que ce joueur s'est déconnecté
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'player_disconnected',
                    'player': self.user.username
                }
            )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'move':
            await self.handle_move(data)
        elif action == 'forfeit':
            await self.handle_forfeit()
    
    async def handle_move(self, data):
        """Gérer un mouvement de pion avec validation serveur"""
        from_row = data.get('from_row')
        from_col = data.get('from_col')
        to_row = data.get('to_row')
        to_col = data.get('to_col')

        game = await self.get_game()

        # Vérifier que c'est le tour du joueur
        if not game.is_player_turn(self.user):
            await self.send_error("Ce n'est pas votre tour")
            return

        # Convertir row/col en positions string
        from_pos = f"{from_row}{from_col}"
        to_pos = f"{to_row}{to_col}"

        # Utiliser la validation de views.py (règles internationales)
        is_valid = await self.validate_move_sync(game, from_pos, to_pos, self.user)
        if not is_valid:
            await self.send_error("Mouvement invalide")
            return

        # Exécuter le mouvement avec la logique de views.py
        await self.execute_move_sync(game, from_pos, to_pos, self.user)

        # Sauvegarder le jeu
        await self.save_game(game)

        # Vérifier la victoire
        await self.check_victory(game)

        # Envoyer le nouvel état
        await self.send_game_state()

    @database_sync_to_async
    def validate_move_sync(self, game, from_pos, to_pos, user):
        """Wrapper synchrone pour is_valid_move"""
        from .views import is_valid_move
        return is_valid_move(game, from_pos, to_pos, user)

    @database_sync_to_async
    def execute_move_sync(self, game, from_pos, to_pos, user):
        """Wrapper synchrone pour execute_move"""
        from .views import execute_move
        execute_move(game, from_pos, to_pos, user)
    
    async def validate_move(self, game, from_row, from_col, to_row, to_col):
        """Valider un mouvement selon les règles de dames"""
        board = game.board_state

        # Vérifier que les positions sont valides (plateau 10x10)
        if not (0 <= from_row < 10 and 0 <= from_col < 10):
            return {'valid': False, 'error': 'Position de départ invalide'}
        if not (0 <= to_row < 10 and 0 <= to_col < 10):
            return {'valid': False, 'error': 'Position d\'arrivée invalide'}
        
        # Vérifier que la case de départ contient un pion du joueur
        from_pos = f"{from_row}{from_col}"
        piece = board.get(from_pos)
        
        if not piece:
            return {'valid': False, 'error': 'Aucun pion à cette position'}
        
        # Déterminer la couleur du joueur
        if game.player1 == self.user:
            player_color = 'b'  # Black
        else:
            player_color = 'w'  # White
        
        # Vérifier que le pion appartient au joueur
        if piece.lower() != player_color:
            return {'valid': False, 'error': 'Ce pion ne vous appartient pas'}
        
        is_king = piece.upper() in ['B', 'W']
        
        # Vérifier que la case d'arrivée est vide
        to_pos = f"{to_row}{to_col}"
        if board.get(to_pos):
            return {'valid': False, 'error': 'La case d\'arrivée n\'est pas vide'}
        
        # Vérifier le mouvement diagonal
        row_diff = to_row - from_row
        col_diff = abs(to_col - from_col)
        
        if col_diff != abs(row_diff):
            return {'valid': False, 'error': 'Mouvement non diagonal'}
        
        # Pour les pions normaux, vérifier la direction
        if not is_king:
            if player_color == 'b' and row_diff > 0:  # Black avance vers le haut (row diminue)
                return {'valid': False, 'error': 'Direction invalide pour ce pion'}
            if player_color == 'w' and row_diff < 0:  # White avance vers le bas (row augmente)
                return {'valid': False, 'error': 'Direction invalide pour ce pion'}
        
        # Vérifier s'il s'agit d'une capture
        capture = False
        if abs(row_diff) == 2:
            # Vérifier la capture
            mid_row = (from_row + to_row) // 2
            mid_col = (from_col + to_col) // 2
            mid_pos = f"{mid_row}{mid_col}"
            mid_piece = board.get(mid_pos)
            
            if not mid_piece:
                return {'valid': False, 'error': 'Aucun pion à capturer'}
            
            # Vérifier que le pion à capturer appartient à l'adversaire
            opponent_color = 'w' if player_color == 'b' else 'b'
            if mid_piece.lower() != opponent_color:
                return {'valid': False, 'error': 'Vous ne pouvez pas capturer votre propre pion'}
            
            capture = True
        elif abs(row_diff) != 1:
            return {'valid': False, 'error': 'Distance invalide'}
        
        # Vérifier si une capture est obligatoire
        mandatory_captures = await self.find_mandatory_captures(game, player_color)
        if mandatory_captures and not capture:
            return {'valid': False, 'error': 'Une capture est obligatoire'}
        
        return {
            'valid': True,
            'capture': capture,
            'is_king': is_king,
            'player_color': player_color
        }
    
    async def find_mandatory_captures(self, game, player_color):
        """Trouver les captures obligatoires pour un joueur"""
        board = game.board_state
        mandatory = []

        for row in range(10):
            for col in range(10):
                pos = f"{row}{col}"
                piece = board.get(pos)

                if piece and piece.lower() == player_color:
                    # Vérifier les captures possibles depuis cette position
                    captures = await self.get_possible_captures(board, row, col, piece)
                    if captures:
                        mandatory.extend(captures)

        return mandatory
    
    async def get_possible_captures(self, board, row, col, piece):
        """Obtenir les captures possibles depuis une position"""
        captures = []
        is_king = piece.upper() in ['B', 'W']
        color = piece.lower()
        
        # Directions possibles selon le type de pion
        if is_king:
            directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
        elif color == 'b':
            directions = [(-2, -2), (-2, 2)]  # Black avance vers le haut
        else:
            directions = [(2, -2), (2, 2)]  # White avance vers le bas
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 10 and 0 <= new_col < 10:
                mid_row, mid_col = row + dr // 2, col + dc // 2
                mid_pos = f"{mid_row}{mid_col}"
                new_pos = f"{new_row}{new_col}"
                
                mid_piece = board.get(mid_pos)
                new_piece = board.get(new_pos)
                
                if mid_piece and mid_piece.lower() != color and not new_piece:
                    captures.append({
                        'from': {'row': row, 'col': col},
                        'to': {'row': new_row, 'col': new_col},
                        'capture': {'row': mid_row, 'col': mid_col}
                    })
        
        return captures
    
    async def check_additional_captures(self, game, row, col):
        """Vérifier si des captures supplémentaires sont possibles"""
        board = game.board_state
        pos = f"{row}{col}"
        piece = board.get(pos)
        
        if not piece:
            return []
        
        captures = await self.get_possible_captures(board, row, col, piece)
        return captures
    
    async def execute_move(self, game, from_row, from_col, to_row, to_col, validation):
        """Exécuter le mouvement sur le plateau"""
        board = game.board_state
        from_pos = f"{from_row}{from_col}"
        to_pos = f"{to_row}{to_col}"
        
        # Déplacer le pion
        piece = board[from_pos]
        board[to_pos] = piece
        board[from_pos] = None
        
        # Gérer la capture
        if validation['capture']:
            mid_row = (from_row + to_row) // 2
            mid_col = (from_col + to_col) // 2
            mid_pos = f"{mid_row}{mid_col}"
            board[mid_pos] = None
        
        # Gérer la promotion en dame (plateau 10x10)
        if not validation['is_king']:
            if validation['player_color'] == 'w' and to_row == 9:
                board[to_pos] = 'W'
            elif validation['player_color'] == 'b' and to_row == 0:
                board[to_pos] = 'B'
        
        # Mettre à jour le plateau
        game.board_state = board
        game.last_move_at = timezone.now()
        
        # Ajouter à l'historique
        game.move_history.append({
            'from': {'row': from_row, 'col': from_col},
            'to': {'row': to_row, 'col': to_col},
            'capture': validation['capture'],
            'player': self.user.username
        })
        
        await self.save_game(game)
    
    async def switch_turn(self, game):
        """Changer de tour"""
        game.current_turn = 2 if game.current_turn == 1 else 1
        await self.save_game(game)
    
    async def check_victory(self, game):
        """Vérifier si un joueur a gagné"""
        board = game.board_state
        
        # Compter les pions de chaque joueur
        black_count = sum(1 for piece in board.values() if piece and piece.lower() == 'b')
        white_count = sum(1 for piece in board.values() if piece and piece.lower() == 'w')
        
        if black_count == 0:
            game.winner = game.player2
            game.status = 'finished'
            await self.save_game(game)
            await game.release_funds_to_winner()
        elif white_count == 0:
            game.winner = game.player1
            game.status = 'finished'
            await self.save_game(game)
            await game.release_funds_to_winner()
    
    async def handle_forfeit(self):
        """Gérer l'abandon de partie"""
        game = await self.get_game()
        if not game:
            return

        # L'autre joueur gagne
        if game.player1 == self.user:
            game.winner = game.player2
            loser = game.player1
        else:
            game.winner = game.player1
            loser = game.player2

        game.status = 'finished'
        await self.save_game(game)

        # Libérer les fonds au gagnant
        await self.release_funds_sync(game)

        # Récupérer les soldes avec database_sync_to_async
        winner_balance = await self.get_winner_balance(game)
        loser_balance = await self.get_loser_balance(loser)

        # Envoyer le résultat à tous les joueurs
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'game_finished',
                'winner': game.winner.username,
                'loser': loser.username,
                'stake': str(game.stake),
                'winner_balance': str(winner_balance),
                'loser_balance': str(loser_balance)
            }
        )

    @database_sync_to_async
    def release_funds_sync(self, game):
        """Wrapper synchrone pour release_funds_to_winner"""
        game.release_funds_to_winner()
        
    @database_sync_to_async
    def get_winner_balance(self, game):
        """Récupérer le solde du gagnant"""
        return game.winner.wallet.balance
        
    @database_sync_to_async
    def get_loser_balance(self, loser):
        """Récupérer le solde du perdant"""
        return loser.wallet.balance
        
    async def send_game_state(self):
        """Envoyer l'état du jeu à tous les joueurs"""
        game = await self.get_game()
        
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'game_update',
                'game_state': {
                    'game_id': str(game.id),
                    'status': game.status,
                    'board_state': game.board_state,
                    'current_turn': game.current_turn,
                    'player1': game.player1.username,
                    'player2': game.player2.username if game.player2 else None,
                    'winner': game.winner.username if game.winner else None,
                    'last_move_at': game.last_move_at.isoformat() if game.last_move_at else None,
                    'move_history': game.move_history
                }
            }
        )
    
    async def send_error(self, message):
        """Envoyer un message d'erreur"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    async def send_message(self, message):
        """Envoyer un message au client"""
        await self.send(text_data=json.dumps(message))
    
    async def game_update(self, event):
        """Handler pour les mises à jour du jeu"""
        await self.send(text_data=json.dumps({
            'type': 'game_update',
            'game_state': event['game_state']
        }))

    async def player_disconnected(self, event):
        """Handler pour la déconnexion d'un joueur"""
        await self.send(text_data=json.dumps({
            'type': 'player_disconnected',
            'player': event['player']
        }))

    async def game_finished(self, event):
        """Handler pour la fin de partie"""
        await self.send(text_data=json.dumps({
            'type': 'game_finished',
            'winner': event['winner'],
            'loser': event['loser'],
            'stake': event['stake'],
            'winner_balance': event['winner_balance'],
            'loser_balance': event['loser_balance']
        }))
    
    @database_sync_to_async
    def get_game(self):
        """Récupérer le jeu depuis la base de données avec relations préchargées"""
        try:
            return Game.objects.select_related('player1', 'player2', 'winner').get(id=self.game_id)
        except Game.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_game(self, game):
        """Sauvegarder le jeu dans la base de données"""
        game.save()
