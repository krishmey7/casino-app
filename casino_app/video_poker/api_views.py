from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import VideoPokerGame
from .serializers import VideoPokerGameSerializer
from casino_app.wallet.models import Wallet

class VideoPokerGameViewSet(viewsets.ModelViewSet):
    queryset = VideoPokerGame.objects.all()
    serializer_class = VideoPokerGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            bet_amount = Decimal(str(request.data.get('bet_amount', '50.00')))
            hold_indices = request.data.get('hold_indices', [])
            
            if bet_amount <= 0:
                return Response({'error': 'Bet amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not isinstance(hold_indices, list) or len(hold_indices) > 5:
                return Response({'error': 'Invalid hold indices'}, status=status.HTTP_400_BAD_REQUEST)
            
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            if wallet.balance < bet_amount:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = VideoPokerGame.objects.create(player=user, bet_amount=bet_amount)
            
            try:
                wallet.debit(bet_amount, description='Mise Video Poker')
            except ValueError as e:
                game.delete()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            game.play_game(hold_indices)
            if game.result == 'win':
                wallet.credit(game.winnings, description='Gain Video Poker')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)