from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import ScratchCardGame
from .serializers import ScratchCardGameSerializer
from casino_app.wallet.models import Wallet

class ScratchCardGameViewSet(viewsets.ModelViewSet):
    queryset = ScratchCardGame.objects.all()
    serializer_class = ScratchCardGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            bet_amount = Decimal(str(request.data.get('bet_amount', '50.00')))
            card_type = request.data.get('card_type', 'classic')
            
            if bet_amount <= 0:
                return Response({'error': 'Bet amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            if card_type not in ['classic', 'deluxe', 'premium']:
                return Response({'error': 'Invalid card type'}, status=status.HTTP_400_BAD_REQUEST)
            
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            if wallet.balance < bet_amount:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            game = ScratchCardGame.objects.create(player=user, bet_amount=bet_amount, card_type=card_type)
            
            try:
                wallet.debit(bet_amount, description='Mise Scratch Cards')
            except ValueError as e:
                game.delete()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            game.play_game()
            if game.result == 'win':
                wallet.credit(game.winnings, description='Gain Scratch Cards')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)