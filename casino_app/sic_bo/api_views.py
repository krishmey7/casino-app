from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import SicBoGame
from .serializers import SicBoGameSerializer
from casino_app.wallet.models import Wallet

class SicBoGameViewSet(viewsets.ModelViewSet):
    queryset = SicBoGame.objects.all()
    serializer_class = SicBoGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        """Crée et joue une partie de Sic Bo"""
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            bet_amount = Decimal(str(request.data.get('bet_amount', '100.00')))
            bet_type = request.data.get('bet_type', 'small')
            
            if bet_amount <= 0:
                return Response({'error': 'Bet amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            if wallet.balance < bet_amount:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = SicBoGame.objects.create(
                player=user,
                bet_amount=bet_amount,
                bet_type=bet_type
            )
            
            try:
                wallet.debit(bet_amount, description='Mise Sic Bo')
            except ValueError as e:
                game.delete()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            game.roll_dice()
            
            if game.result == 'win':
                wallet.credit(game.winnings, description='Gain Sic Bo')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)