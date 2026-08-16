from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import CrapsGame
from .serializers import CrapsGameSerializer
from casino_app.wallet.models import Wallet

class CrapsGameViewSet(viewsets.ModelViewSet):
    queryset = CrapsGame.objects.all()
    serializer_class = CrapsGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        """Crée et démarre une partie de craps"""
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            bet_amount = Decimal(str(request.data.get('bet_amount', '100.00')))
            bet_type = request.data.get('bet_type', 'pass')
            
            if bet_amount <= 0:
                return Response({'error': 'Bet amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            if wallet.balance < bet_amount:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = CrapsGame.objects.create(
                player=user,
                bet_amount=bet_amount,
                bet_type=bet_type
            )
            game.roll_dice()
            
            try:
                wallet.debit(bet_amount, description='Mise Craps')
            except ValueError as e:
                game.delete()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            if game.status == 'finished':
                if game.result == 'win':
                    wallet.credit(game.winnings, description='Gain Craps')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def roll_again(self, request, pk=None):
        """Lance les dés à nouveau"""
        try:
            game = self.get_object()
            
            if game.status == 'finished':
                return Response({'error': 'Game already finished'}, status=status.HTTP_400_BAD_REQUEST)
            
            game.roll_dice()
            
            if game.status == 'finished' and game.result == 'win':
                wallet, _ = Wallet.objects.get_or_create(utilisateur=game.player)
                wallet.credit(game.winnings, description='Gain Craps')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)