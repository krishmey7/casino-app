"""
WebSocket Consumer pour LUDO
Gère la communication temps réel entre les joueurs
"""

import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import LudoGame, LudoPlayer
from .services import GameEngineService, TimeoutService, GameService


class LudoGameConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket pour le jeu LUDO"""
    
    async def connect(self):
        """Gérer la connexion WebSocket"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Récupérer l'ID du jeu depuis l'URL
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'ludo_game_{self.game_id}'
        
        # Vérifier que l'utilisateur est dans la partie
        try:
            player = await database_sync_to_async(LudoPlayer.objects.get)(
                game__id=self.game_id, user=self.user
            )
            self.player_color = player.color
        except LudoPlayer.DoesNotExist:
            await self.close()
            return
        
        # Rejoindre le groupe de la partie
        await self.channel_layer.group_add(self.game_group_name, self.channel_name)
        
        # Marquer le joueur comme connecté
        await self.mark_player_connected()
        
        await self.accept()
        
        # Envoyer l'état actuel du jeu après acceptation seulement si la partie est active
        game = await self.get_game()
        if game and game.status == 'active':
            await self.send_game_state()
        
        # Notifier les autres joueurs (sauf celui qui vient de se connecter)
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'player_joined',
                'player': self.user.username,
                'exclude': self.channel_name
            }
        )
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket"""
        # Quitter le groupe WebSocket
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)
        
        # Marquer le joueur comme déconnecté
        await self.mark_player_disconnected()
        
        # Notifier les autres joueurs
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'player_disconnected',
                'player': self.user.username
            }
        )
    
    async def receive(self, text_data):
        """Réception des messages du client"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'roll_dice':
            await self.handle_roll_dice(data)
        elif message_type == 'move_token':
            await self.handle_move_token(data)
        elif message_type == 'skip_turn':
            await self.handle_skip_turn(data)
        elif message_type == 'mark_ready':
            await self.handle_mark_ready(data)
        elif message_type == 'leave_game':
            await self.handle_leave_game(data)
    
    async def handle_roll_dice(self, data):
        """Gérer le lancer de dés"""
        game = await self.get_game()
        
        if not game or game.status != 'active':
            await self.send_error("La partie n'est pas active")
            return
        
        # Vérifier que c'est le tour du joueur
        current_player = await self.get_current_player(game)
        if not current_player or current_player.user != self.user:
            await self.send_error("Ce n'est pas votre tour")
            return
        
        # Lancer les dés
        dice_result = await database_sync_to_async(GameEngineService.roll_dice_and_save)(game)
        
        # Envoyer le résultat à tous les joueurs
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'dice_rolled',
                'player': self.user.username,
                'dice': dice_result
            }
        )
        
        # Vérifier si le joueur a des mouvements possibles
        valid_moves = await database_sync_to_async(GameEngineService.get_valid_moves_for_current_turn)(game)
        
        if not valid_moves:
            # Pas de mouvements possibles, passer le tour automatiquement
            await self.handle_skip_turn(data)
    
    async def handle_move_token(self, data):
        """Gérer le mouvement d'un pion"""
        game = await self.get_game()
        
        if not game or game.status != 'active':
            await self.send_error("La partie n'est pas active")
            return
        
        # Vérifier que c'est le tour du joueur
        current_player = await self.get_current_player(game)
        if not current_player or current_player.user != self.user:
            await self.send_error("Ce n'est pas votre tour")
            return
        
        token_index = data.get('token_index')
        if token_index is None or token_index < 0 or token_index > 3:
            await self.send_error("Index de pion invalide")
            return
        
        # Exécuter le mouvement
        result = await database_sync_to_async(
            GameEngineService.execute_move_and_save
        )(game, current_player.color, token_index)
        
        if not result['success']:
            await self.send_error(result.get('error', 'Mouvement invalide'))
            return
        
        # Envoyer le résultat à tous les joueurs
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'token_moved',
                'player': self.user.username,
                'color': current_player.color,
                'move': result['move'],
                'extra_turn': result['extra_turn'],
                'captured': result.get('captured'),
                'victory': result.get('victory', False),
                'winner': result.get('winner')
            }
        )
        
        # Si pas de tour supplémentaire et pas de victoire, passer au tour suivant
        if not result['extra_turn'] and not result.get('victory'):
            await self.advance_turn(game)
    
    async def handle_skip_turn(self, data):
        """Gérer le passage de tour"""
        game = await self.get_game()
        
        if not game or game.status != 'active':
            await self.send_error("La partie n'est pas active")
            return
        
        # Vérifier que c'est le tour du joueur
        current_player = await self.get_current_player(game)
        if not current_player or current_player.user != self.user:
            await self.send_error("Ce n'est pas votre tour")
            return
        
        # Passer au tour suivant
        await self.advance_turn(game)
        
        # Notifier les joueurs
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'turn_skipped',
                'player': self.user.username
            }
        )
    
    async def handle_mark_ready(self, data):
        """Marquer le joueur comme prêt"""
        game = await self.get_game()
        
        if not game or game.status != 'waiting':
            await self.send_error("La partie n'est pas en attente")
            return
        
        # Marquer le joueur comme prêt
        await database_sync_to_async(self.mark_player_ready)()
        
        # Notifier les autres joueurs que ce joueur est prêt
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'player_ready',
                'player': self.user.username
            }
        )
        
        # Vérifier si la partie peut démarrer automatiquement
        game = await self.get_game()
        if game and await database_sync_to_async(game.can_start)():
            # Démarrer la partie
            await database_sync_to_async(GameService.start_game)(game)
            
            # Notifier les joueurs que la partie a démarré
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_started',
                    'game_id': str(game.id)
                }
            )
    
    async def handle_leave_game(self, data):
        """Gérer le départ d'un joueur"""
        game = await self.get_game()
        
        if not game:
            await self.send_error("Partie introuvable")
            return
        
        # Annuler ou gérer l'abandon
        if game.status == 'waiting':
            await database_sync_to_async(GameService.cancel_game)(game, self.user)
        elif game.status == 'active':
            await database_sync_to_async(GameService.handle_forfeit)(game, self.user)
        
        # Notifier les joueurs
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'game_cancelled',
                'player': self.user.username,
                'reason': 'left_game'
            }
        )
    
    async def advance_turn(self, game):
        """Passe au tour suivant"""
        new_turn = await database_sync_to_async(GameEngineService.advance_turn)(game)
        
        # Récupérer le nouveau joueur actuel
        players = await database_sync_to_async(list)(game.ludoplayers.all().order_by('turn_order'))
        new_player = players[new_turn] if new_turn < len(players) else None
        
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'turn_changed',
                'current_turn': new_turn,
                'current_player': new_player.user.username if new_player else None,
                'current_color': new_player.color if new_player else None
            }
        )
    
    async def start_game(self, game):
        """Démarre la partie"""
        await database_sync_to_async(GameService.start_game)(game)
        
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'game_started'
            }
        )
    
    # Handlers de messages du groupe
    
    async def dice_rolled(self, event):
        """Envoyer le résultat des dés"""
        await self.send(text_data=json.dumps({
            'type': 'dice_rolled',
            'player': event['player'],
            'dice': event['dice']
        }))
    
    async def token_moved(self, event):
        """Envoyer le mouvement de pion"""
        await self.send(text_data=json.dumps({
            'type': 'token_moved',
            'player': event['player'],
            'color': event['color'],
            'move': event['move'],
            'extra_turn': event['extra_turn'],
            'captured': event.get('captured'),
            'victory': event.get('victory', False),
            'winner': event.get('winner')
        }))
    
    async def turn_changed(self, event):
        """Envoyer le changement de tour"""
        await self.send(text_data=json.dumps({
            'type': 'turn_changed',
            'current_turn': event['current_turn'],
            'current_player': event['current_player'],
            'current_color': event['current_color']
        }))
    
    async def turn_skipped(self, event):
        """Envoyer le passage de tour"""
        await self.send(text_data=json.dumps({
            'type': 'turn_skipped',
            'player': event['player']
        }))
    
    async def player_joined(self, event):
        """Envoyer la notification de joueur rejoint"""
        # Ne pas envoyer le message au joueur qui vient de se connecter
        if event.get('exclude') == self.channel_name:
            return
        
        await self.send(text_data=json.dumps({
            'type': 'player_joined',
            'player': event['player']
        }))
    
    async def player_disconnected(self, event):
        """Envoyer la notification de joueur déconnecté"""
        await self.send(text_data=json.dumps({
            'type': 'player_disconnected',
            'player': event['player']
        }))
    
    async def player_ready(self, event):
        """Envoyer la notification de joueur prêt"""
        await self.send(text_data=json.dumps({
            'type': 'player_ready',
            'player': event['player']
        }))
    
    async def game_started(self, event):
        """Envoyer la notification de jeu démarré"""
        await self.send(text_data=json.dumps({
            'type': 'game_started'
        }))
    
    async def game_cancelled(self, event):
        """Envoyer la notification de jeu annulé"""
        await self.send(text_data=json.dumps({
            'type': 'game_cancelled',
            'player': event['player'],
            'reason': event['reason']
        }))
    
    # Méthodes auxiliaires
    
    @database_sync_to_async
    def check_authorization(self):
        """Vérifier que l'utilisateur est un joueur de la partie"""
        try:
            game = LudoGame.objects.get(id=self.game_id)
            return LudoPlayer.objects.filter(game=game, user=self.user).exists()
        except LudoGame.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_game(self):
        """Récupérer la partie"""
        try:
            return LudoGame.objects.select_related('winner').get(id=self.game_id)
        except LudoGame.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_player(self):
        """Récupérer le joueur"""
        try:
            game = LudoGame.objects.get(id=self.game_id)
            return LudoPlayer.objects.get(game=game, user=self.user)
        except (LudoGame.DoesNotExist, LudoPlayer.DoesNotExist):
            return None
    
    @database_sync_to_async
    def get_current_player(self, game):
        """Récupérer le joueur actuel"""
        players = list(game.ludoplayers.all().order_by('turn_order'))
        if game.current_turn < len(players):
            return players[game.current_turn]
        return None
    
    @database_sync_to_async
    def mark_player_connected(self):
        """Marquer le joueur comme connecté"""
        try:
            game = LudoGame.objects.get(id=self.game_id)
            player = LudoPlayer.objects.get(game=game, user=self.user)
            player.mark_connected()
        except (LudoGame.DoesNotExist, LudoPlayer.DoesNotExist):
            pass
    
    @database_sync_to_async
    def mark_player_disconnected(self):
        """Marquer le joueur comme déconnecté"""
        try:
            game = LudoGame.objects.get(id=self.game_id)
            player = LudoPlayer.objects.get(game=game, user=self.user)
            player.mark_disconnected()
        except (LudoGame.DoesNotExist, LudoPlayer.DoesNotExist):
            pass
    
    @database_sync_to_async
    def mark_player_ready(self):
        """Marquer le joueur comme prêt"""
        try:
            game = LudoGame.objects.get(id=self.game_id)
            player = LudoPlayer.objects.get(game=game, user=self.user)
            player.mark_ready()
        except (LudoGame.DoesNotExist, LudoPlayer.DoesNotExist):
            pass
    
    async def send_game_state(self):
        """Envoyer l'état complet du jeu"""
        game = await self.get_game()
        if not game:
            return
        
        try:
            @database_sync_to_async
            def get_players_data():
                # Utiliser values() pour éviter les requêtes N+1 et les problèmes async
                from django.db import connection
                players = list(game.ludoplayers.values(
                    'user__username',
                    'color',
                    'turn_order',
                    'is_connected',
                    'is_ready'
                ))
                return [
                    {
                        'username': p['user__username'],
                        'color': p['color'],
                        'turn_order': p['turn_order'],
                        'is_connected': p['is_connected'],
                        'is_ready': p['is_ready']
                    }
                    for p in players
                ]
            
            players_data = await get_players_data()
            
            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'game': {
                    'id': str(game.id),
                    'status': game.status,
                    'current_turn': game.current_turn,
                    'stake': str(game.stake),
                    'game_state': game.game_state,
                    'winner': game.winner.username if game.winner else None
                },
                'players': players_data
            }))
        except Exception as e:
            # En cas d'erreur, envoyer un état minimal sans les données des joueurs
            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'game': {
                    'id': str(game.id),
                    'status': game.status,
                    'current_turn': game.current_turn,
                    'stake': str(game.stake),
                    'game_state': game.game_state,
                    'winner': game.winner.username if game.winner else None
                },
                'players': []
            }))
    
    async def send_error(self, message):
        """Envoyer un message d'erreur"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
