from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import LetItRideGame
from .serializers import LetItRideGameSerializer
from casino_app.wallet.models import Wallet

class LetItRideGameViewSet(viewsets.ModelViewSet):
    queryset = LetItRideGame.objects.all()
    serializer_class = LetItRideGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            bet_amount = Decimal(str(request.data.get('bet_amount', '50.00')))
            side_bet = Decimal(str(request.data.get('side_bet', '0.00')))
            
            if bet_amount <= 0:
                return Response({'error': 'Bet amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            total_bet = bet_amount + side_bet
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            if wallet.balance < total_bet:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = LetItRideGame.objects.create(player=user, bet_amount=bet_amount, side_bet=side_bet)
            
            try:
                wallet.debit(total_bet, description='Mise Let It Ride')
            except ValueError as e:
                game.delete()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            game.play_game()
            if game.result == 'win':
                wallet.credit(game.winnings, description='Gain Let It Ride')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)