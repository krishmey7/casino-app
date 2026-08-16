import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import FaceOuPileGame


class FaceOuPileGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'face_ou_pile_{self.game_id}'

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
            game = FaceOuPileGame.objects.select_related('player1', 'player2').get(id=self.game_id)
            return game.player1 == self.user or game.player2 == self.user
        except FaceOuPileGame.DoesNotExist:
            return False

    async def disconnect(self, close_code):
        # Quitter le groupe WebSocket
        await self.channel_layer.group_discard(self.game_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'request_rematch':
            await self.handle_rematch_request()
        elif action == 'accept_rematch':
            await self.handle_rematch_accept()
        elif action == 'decline_rematch':
            await self.handle_rematch_decline()

    async def handle_rematch_request(self):
        """Un joueur demande une revanche"""
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'rematch_requested',
                'requester': self.user.username,
            }
        )

    async def handle_rematch_accept(self):
        """L'autre joueur accepte la revanche - créer une nouvelle partie"""
        game = await self.get_game()
        if not game:
            return
        
        # Créer une nouvelle partie avec les mêmes joueurs et mise
        new_game = await self.create_rematch_game(game)
        
        if new_game:
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'rematch_accepted',
                    'new_game_id': new_game.id,
                    'requester': self.user.username,
                }
            )

    async def handle_rematch_decline(self):
        """L'autre joueur refuse la revanche"""
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'rematch_declined',
                'decliner': self.user.username,
            }
        )

    @database_sync_to_async
    def create_rematch_game(self, old_game):
        """Crée une nouvelle partie de revanche avec les mêmes paramètres"""
        from .models import FaceOuPileGame
        from casino_app.wallet.models import Wallet
        from django.db import transaction
        
        with transaction.atomic():
            # Déduire la mise des wallets des deux joueurs
            p1_wallet = Wallet.objects.get(utilisateur=old_game.player1)
            p2_wallet = Wallet.objects.get(utilisateur=old_game.player2)
            
            p1_wallet.debit(old_game.bet_amount, 'Mise pour Face ou Pile BO3 (Revanche)')
            p2_wallet.debit(old_game.bet_amount, 'Mise pour Face ou Pile BO3 (Revanche)')
            
            # Inverser les rôles pour varier qui commence la manche 1
            new_game = FaceOuPileGame.objects.create(
                player1=old_game.player2,  # L'ancien player2 devient player1
                player2=old_game.player1,  # L'ancien player1 devient player2
                bet_amount=old_game.bet_amount,
                status='playing',  # Directement en 'playing' car les 2 joueurs sont présents
                player1_score=0,
                player2_score=0,
                current_round=1,
                round_chooser='player1',  # Le nouveau player1 (ancien player2) commence
                round_results=[],
            )
            new_game.setup_round()
            new_game.save()
        
        return new_game

    async def send_game_state(self):
        """Envoyer l'état du jeu à tous les joueurs"""
        game = await self.get_game()
        
        if not game:
            return
        
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'game_update',
                'game_state': {
                    'game_id': str(game.id),
                    'status': game.status,
                    'player1': game.player1.username,
                    'player2': game.player2.username if game.player2 else None,
                    'player1_score': game.player1_score,
                    'player2_score': game.player2_score,
                    'current_round': game.current_round,
                    'round_chooser': game.round_chooser,
                    'coin_result': game.coin_result,
                    'winner': game.winner.username if game.winner else None,
                    'round_results': game.round_results,
                }
            }
        )

    async def game_flip_start(self, event):
        """Handler pour le début de l'animation de pièce (broadcast à tous les joueurs)"""
        await self.send(text_data=json.dumps({
            'type': 'game_flip_start',
            'result': event['result'],
            'chooser': event['chooser'],
            'chooser_choice': event['chooser_choice'],
            'round': event['round'],
            'player1_score': event['player1_score'],
            'player2_score': event['player2_score'],
            'round_winner': event.get('round_winner'),  # FIX: Relai du nom du gagnant
            'is_game_over': event.get('is_game_over', False)
        }))

    async def game_update(self, event):
        """Handler pour les mises à jour du jeu"""
        await self.send(text_data=json.dumps({
            'type': 'game_update',
            'game_state': event['game_state']
        }))

    async def game_finished(self, event):
        """Handler pour la fin de partie"""
        await self.send(text_data=json.dumps({
            'type': 'game_finished',
            'winner': event['winner'],
            'player1_score': event['player1_score'],
            'player2_score': event['player2_score'],
            'bet_amount': event['bet_amount'],
        }))

    async def rematch_requested(self, event):
        """Handler pour la demande de revanche"""
        await self.send(text_data=json.dumps({
            'type': 'rematch_requested',
            'requester': event['requester'],
        }))

    async def rematch_accepted(self, event):
        """Handler pour l'acceptation de revanche"""
        await self.send(text_data=json.dumps({
            'type': 'rematch_accepted',
            'new_game_id': event['new_game_id'],
            'requester': event['requester'],
        }))

    async def rematch_declined(self, event):
        """Handler pour le refus de revanche"""
        await self.send(text_data=json.dumps({
            'type': 'rematch_declined',
            'decliner': event['decliner'],
        }))

    @database_sync_to_async
    def get_game(self):
        """Récupérer le jeu depuis la base de données avec relations préchargées"""
        try:
            return FaceOuPileGame.objects.select_related('player1', 'player2', 'winner').get(id=self.game_id)
        except FaceOuPileGame.DoesNotExist:
            return None
