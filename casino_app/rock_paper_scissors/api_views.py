from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
from .models import RockPaperScissorsGame
from .serializers import RockPaperScissorsGameSerializer
from casino_app.wallet.models import Wallet


class RockPaperScissorsGameViewSet(viewsets.ModelViewSet):
    queryset = RockPaperScissorsGame.objects.all()
    serializer_class = RockPaperScissorsGameSerializer
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
            wallet.debit(bet_amount, 'Mise pour Pierre-Papier-Ciseaux')
            game = RockPaperScissorsGame.objects.create(player1=request.user, bet_amount=bet_amount)
        serializer = self.get_serializer(game)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def join_game(self, request, pk=None):
        game = get_object_or_404(RockPaperScissorsGame, pk=pk)
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
            wallet.debit(bet_amount, 'Mise pour Pierre-Papier-Ciseaux')
            game.player2 = request.user
            game.status = 'playing'
            game.save()
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel_game(self, request, pk=None):
        game = get_object_or_404(RockPaperScissorsGame, pk=pk)
        if game.player1 != request.user:
            return Response({'error': 'Seul le créateur peut annuler la partie.'}, status=status.HTTP_403_FORBIDDEN)
        if game.status != 'waiting':
            return Response({'error': 'Seule une partie en attente peut être annulée.'}, status=status.HTTP_400_BAD_REQUEST)

        wallet, _ = Wallet.objects.get_or_create(utilisateur=request.user)
        with transaction.atomic():
            wallet.credit(game.bet_amount, 'Annulation partie Pierre-Papier-Ciseaux')
            game.delete()

        return Response({'detail': 'Partie annulée.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def make_choice(self, request, pk=None):
        game = get_object_or_404(RockPaperScissorsGame, pk=pk, status='playing')
        choice = request.data.get('choice')
        if choice not in ['rock', 'paper', 'scissors']:
            return Response({'error': 'Invalid choice'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user == game.player1 and not game.player1_choice:
            game.player1_choice = choice
        elif request.user == game.player2 and not game.player2_choice:
            game.player2_choice = choice
        else:
            return Response({'error': 'Already chose or not your turn'}, status=status.HTTP_400_BAD_REQUEST)

        game.save()

        if game.player1_choice and game.player2_choice:
            winner = game.determine_winner()
            if winner == 'draw':
                # Refund bets
                p1_wallet = Wallet.objects.get(utilisateur=game.player1)
                p2_wallet = Wallet.objects.get(utilisateur=game.player2)
                p1_wallet.credit(game.bet_amount, 'Remise égalité Pierre-Papier-Ciseaux')
                p2_wallet.credit(game.bet_amount, 'Remise égalité Pierre-Papier-Ciseaux')
                game.status = 'finished'
            else:
                game.winner = winner
                game.payout()
                game.status = 'finished'
            from django.utils import timezone
            game.finished_at = timezone.now()
            game.save()

        serializer = self.get_serializer(game)
        return Response(serializer.data)