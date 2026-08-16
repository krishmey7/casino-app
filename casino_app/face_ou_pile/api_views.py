from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import FaceOuPileGame
from .serializers import FaceOuPileGameSerializer
from casino_app.wallet.models import Wallet


class FaceOuPileGameViewSet(viewsets.ModelViewSet):
    queryset = FaceOuPileGame.objects.all()
    serializer_class = FaceOuPileGameSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def create_game(self, request):
        bet_amount = request.data.get('bet_amount')
        if not bet_amount:
            return Response({'error': 'Bet amount required'}, status=status.HTTP_400_BAD_REQUEST)
        bet_amount = Decimal(str(bet_amount))
        if bet_amount <= 0:
            return Response({'error': 'Bet amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)

        wallet = get_object_or_404(Wallet, utilisateur=request.user)
        if wallet.balance < bet_amount:
            return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            wallet.debit(bet_amount, 'Mise pour Face ou Pile BO3')
            game = FaceOuPileGame.objects.create(
                player1=request.user, 
                bet_amount=bet_amount
            )
            # Configurer la manche 1 (joueur 1 choisit)
            game.setup_round()
            game.save()
        serializer = self.get_serializer(game)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def join_game(self, request, pk=None):
        game = get_object_or_404(FaceOuPileGame, pk=pk)
        if game.player1 == request.user or game.player2 == request.user:
            serializer = self.get_serializer(game)
            return Response(serializer.data)

        if game.status != 'waiting':
            return Response({'error': 'Game is not available for joining'}, status=status.HTTP_400_BAD_REQUEST)
        if game.player2:
            return Response({'error': 'Game already has two players'}, status=status.HTTP_400_BAD_REQUEST)

        bet_amount = game.bet_amount
        wallet = get_object_or_404(Wallet, utilisateur=request.user)
        if wallet.balance < bet_amount:
            return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            wallet.debit(bet_amount, 'Mise pour Face ou Pile BO3')
            game.player2 = request.user
            game.status = 'playing'
            game.save()
        
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel_game(self, request, pk=None):
        game = get_object_or_404(FaceOuPileGame, pk=pk)
        if game.player1 != request.user:
            return Response({'error': 'Seul le créateur peut annuler la partie.'}, status=status.HTTP_403_FORBIDDEN)
        if game.status != 'waiting':
            return Response({'error': 'Seule une partie en attente peut être annulée.'}, status=status.HTTP_400_BAD_REQUEST)

        wallet, _ = Wallet.objects.get_or_create(utilisateur=request.user)
        with transaction.atomic():
            wallet.credit(game.bet_amount, 'Annulation partie Face ou Pile')
            game.delete()

        return Response({'detail': 'Partie annulée.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def make_choice(self, request, pk=None):
        game = get_object_or_404(FaceOuPileGame, pk=pk, status='playing')
        choice = request.data.get('choice')
        if choice not in ['face', 'pile']:
            return Response({'error': 'Invalid choice'}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier que c'est le tour du joueur de choisir
        is_player1 = request.user == game.player1
        is_player2 = request.user == game.player2
        
        if not is_player1 and not is_player2:
            return Response({'error': 'You are not a player in this game'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier que c'est le bon joueur pour cette manche
        if game.round_chooser == 'player1' and not is_player1:
            return Response({'error': 'It is player1\'s turn to choose'}, status=status.HTTP_400_BAD_REQUEST)
        if game.round_chooser == 'player2' and not is_player2:
            return Response({'error': 'It is player2\'s turn to choose'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier que la manche n'a pas déjà un résultat enregistré
        if game.coin_result is not None:
            return Response({'error': 'Round already completed'}, status=status.HTTP_400_BAD_REQUEST)

        # Enregistrer le choix du chooser de la manche
        game.chooser_choice = choice.lower().strip()

        # Effectuer le tirage aléatoire
        game.flip_coin()
        
        # Validation stricte du résultat de la pièce
        if game.coin_result not in ['face', 'pile']:
            # Si le résultat est invalide, forcer un nouveau tirage
            game.flip_coin()
        
        # Capturer le numéro de manche en cours AVANT incrémentation
        current_round_before = game.current_round
        
        # Terminer la manche
        round_winner = game.complete_round()
        game.save()
        
        # Récupérer le nom d'utilisateur du gagnant
        round_winner_username = round_winner.username if round_winner else None

        # Envoyer le message WebSocket pour synchroniser l'animation
        channel_layer = get_channel_layer()
        
        # Validation finale avant envoi WebSocket
        result_to_send = game.coin_result if game.coin_result in ['face', 'pile'] else 'face'
        
        async_to_sync(channel_layer.group_send)(
            f'face_ou_pile_{game.id}',
            {
                'type': 'game_flip_start',
                'result': result_to_send,
                'chooser': game.round_chooser,
                'chooser_choice': game.chooser_choice,  # FIX: Choix normalisé
                'round': current_round_before,  # FIX: Manche active (avant incrémentation)
                'player1_score': game.player1_score,
                'player2_score': game.player2_score,
                'round_winner': round_winner_username,
                'is_game_over': game.status == 'finished',
            }
        )

        # Si la partie est terminée, effectuer le paiement et notifier
        if game.status == 'finished':
            game.payout()
            game.save()
            
            # Envoyer le message de fin de partie
            async_to_sync(channel_layer.group_send)(
                f'face_ou_pile_{game.id}',
                {
                    'type': 'game_finished',
                    'winner': game.winner.username if game.winner else None,
                    'player1_score': game.player1_score,
                    'player2_score': game.player2_score,
                    'bet_amount': str(game.bet_amount),
                }
            )

        serializer = self.get_serializer(game)
        return Response(serializer.data)
