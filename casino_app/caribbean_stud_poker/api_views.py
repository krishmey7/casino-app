from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import CaribbeanStudPokerGame
from .serializers import CaribbeanStudPokerGameSerializer
from casino_app.wallet.models import Wallet

class CaribbeanStudPokerGameViewSet(viewsets.ModelViewSet):
    queryset = CaribbeanStudPokerGame.objects.all()
    serializer_class = CaribbeanStudPokerGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            ante_bet = Decimal(str(request.data.get('ante_bet', '50.00')))
            call_bet = Decimal(str(request.data.get('call_bet', '0.00')))
            
            if ante_bet <= 0:
                return Response({'error': 'Ante bet must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            total_bet = ante_bet + call_bet
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            if wallet.balance < total_bet:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = CaribbeanStudPokerGame.objects.create(player=user, ante_bet=ante_bet, call_bet=call_bet)
            
            try:
                wallet.debit(total_bet, description='Mise Caribbean Stud Poker')
            except ValueError as e:
                game.delete()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            game.play_game()
            if game.result == 'win':
                wallet.credit(game.winnings, description='Gain Caribbean Stud Poker')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)