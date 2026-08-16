from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import PokerGame
from .serializers import PokerGameSerializer
from casino_app.wallet.models import Wallet


class PokerGameViewSet(viewsets.ModelViewSet):
    queryset = PokerGame.objects.all()
    serializer_class = PokerGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        """Crée et démarre une nouvelle partie de poker"""
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            bet_amount = Decimal(str(request.data.get('bet_amount', '100.00')))
            
            # Valider la mise
            if bet_amount <= 0:
                return Response({'error': 'Bet amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier le solde
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            if wallet.balance < bet_amount:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer la partie
            game = PokerGame.objects.create(
                player=user,
                bet_amount=bet_amount
            )
            game.deal_hand()
            
            # Déduire la mise
            try:
                wallet.debit(bet_amount, description='Mise Poker Game')
            except ValueError as e:
                game.delete()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = self.get_serializer(game)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except (ValueError, TypeError) as e:
            return Response({'error': f'Invalid data: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def draw(self, request, pk=None):
        """Tire les cartes avec les indices à garder"""
        try:
            game = self.get_object()
            
            if game.status != 'playing':
                return Response({'error': 'Game not playing'}, status=status.HTTP_400_BAD_REQUEST)
            
            hold_indices = request.data.get('hold', [])
            if not isinstance(hold_indices, list) or len(hold_indices) > 5:
                return Response({'error': 'Invalid hold indices'}, status=status.HTTP_400_BAD_REQUEST)
            
            game.draw_cards(hold_indices)
            
            # Crédit des gains si gagné
            if game.status == 'won':
                wallet, _ = Wallet.objects.get_or_create(utilisateur=game.player)
                wallet.credit(game.winnings, description='Gain Poker Game')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def my_games(self, request):
        """Récupère les parties de poker de l'utilisateur"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        games = PokerGame.objects.filter(player=user).order_by('-created_at')
        serializer = self.get_serializer(games, many=True)
        return Response(serializer.data)