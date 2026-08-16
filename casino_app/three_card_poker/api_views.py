from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import ThreeCardPokerGame
from .serializers import ThreeCardPokerGameSerializer
from casino_app.wallet.models import Wallet

class ThreeCardPokerGameViewSet(viewsets.ModelViewSet):
    queryset = ThreeCardPokerGame.objects.all()
    serializer_class = ThreeCardPokerGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            ante_bet = Decimal(str(request.data.get('ante_bet', '50.00')))
            play_bet = Decimal(str(request.data.get('play_bet', '0.00')))
            
            if ante_bet <= 0:
                return Response({'error': 'Ante bet must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            total_bet = ante_bet + play_bet
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            if wallet.balance < total_bet:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = ThreeCardPokerGame.objects.create(player=user, ante_bet=ante_bet, play_bet=play_bet)
            
            try:
                wallet.debit(total_bet, description='Mise Three Card Poker')
            except ValueError as e:
                game.delete()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            game.play_game()
            if game.result == 'win':
                wallet.credit(game.winnings, description='Gain Three Card Poker')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)