from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import PaiGowGame
from .serializers import PaiGowGameSerializer
from casino_app.wallet.models import Wallet

class PaiGowGameViewSet(viewsets.ModelViewSet):
    queryset = PaiGowGame.objects.all()
    serializer_class = PaiGowGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        """Crée et joue une partie de Pai Gow"""
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            bet_amount = Decimal(str(request.data.get('bet_amount', '100.00')))
            
            if bet_amount <= 0:
                return Response({'error': 'Bet amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            if wallet.balance < bet_amount:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = PaiGowGame.objects.create(
                player=user,
                bet_amount=bet_amount
            )
            
            try:
                wallet.debit(bet_amount, description='Mise Pai Gow')
            except ValueError as e:
                game.delete()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            game.deal_game()
            
            if game.result in ['win', 'tie']:
                wallet.credit(game.winnings, description='Gain Pai Gow')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)