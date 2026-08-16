from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import KenoGame
from .serializers import KenoGameSerializer
from casino_app.wallet.models import Wallet

class KenoGameViewSet(viewsets.ModelViewSet):
    queryset = KenoGame.objects.all()
    serializer_class = KenoGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        """Crée et joue une partie de Keno"""
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            bet_amount = Decimal(str(request.data.get('bet_amount', '100.00')))
            picks = request.data.get('picks', [])
            
            if bet_amount <= 0:
                return Response({'error': 'Bet amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not picks or len(picks) == 0 or len(picks) > 20:
                return Response({'error': 'Vous devez choisir entre 1 et 20 numéros'}, status=status.HTTP_400_BAD_REQUEST)
            
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            if wallet.balance < bet_amount:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = KenoGame.objects.create(
                player=user,
                bet_amount=bet_amount,
                picks=picks
            )
            
            try:
                wallet.debit(bet_amount, description='Mise Keno')
            except ValueError as e:
                game.delete()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            game.play_game()
            
            if game.result == 'win':
                wallet.credit(game.winnings, description='Gain Keno')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)