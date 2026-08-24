from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import RedDogGame
from .serializers import RedDogGameSerializer
from casino_app.wallet.models import Wallet

class RedDogGameViewSet(viewsets.ModelViewSet):
    queryset = RedDogGame.objects.all()
    serializer_class = RedDogGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            bet_amount = Decimal(str(request.data.get('bet_amount', '100.00')))
            bet_type = request.data.get('bet_type', 'spread')
            
            if bet_amount <= 0:
                return Response({'error': 'Bet amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Rafraîchir le wallet depuis la DB pour avoir la balance à jour
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            wallet.refresh_from_db()
            
            if wallet.balance < bet_amount:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Débiter la mise AVANT de jouer (cohérent avec le métier)
            try:
                wallet.debit(bet_amount, description='Mise Red Dog')
                # Recharger le wallet depuis la DB pour avoir la balance à jour
                wallet.refresh_from_db()
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer et jouer la partie
            game = RedDogGame.objects.create(
                player=user,
                bet_amount=bet_amount,
                bet_type=bet_type
            )
            game.play_game()
            
            # Créditer le gain si le joueur a gagné
            if game.result == 'win' and game.winnings and game.winnings > 0:
                wallet.credit(game.winnings, description='Gain Red Dog')
                # Recharger le wallet depuis la DB pour avoir la balance à jour
                wallet.refresh_from_db()
            
            serializer = self.get_serializer(game)
            # Retourner aussi la balance mise à jour pour le frontend
            response_data = dict(serializer.data)
            response_data['new_balance'] = str(wallet.balance)
            response_data['previous_balance'] = str(wallet.balance + bet_amount - (game.winnings if game.result == 'win' else Decimal('0')))
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
