from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import TexasHoldemGame
from .serializers import TexasHoldemGameSerializer
from casino_app.wallet.models import Wallet

class TexasHoldemGameViewSet(viewsets.ModelViewSet):
    queryset = TexasHoldemGame.objects.all()
    serializer_class = TexasHoldemGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            bet_amount = Decimal(str(request.data.get('bet_amount', '50.00')))
            
            if bet_amount <= 0:
                return Response({'error': 'Bet amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            if wallet.balance < bet_amount:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = TexasHoldemGame.objects.create(player=user, bet_amount=bet_amount)
            
            try:
                wallet.debit(bet_amount, description='Mise Texas Holdem')
            except ValueError as e:
                game.delete()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            game.play_game()
            if game.result == 'win':
                wallet.credit(game.winnings, description='Gain Texas Holdem')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)