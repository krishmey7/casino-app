from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import SlotsGame
from .serializers import SlotsGameSerializer
from casino_app.wallet.models import Wallet


class SlotsGameViewSet(viewsets.ModelViewSet):
    queryset = SlotsGame.objects.all()
    serializer_class = SlotsGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        """Crée et démarre une nouvelle partie de slots"""
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
            game = SlotsGame.objects.create(
                player=user,
                bet_amount=bet_amount,
                status='waiting'
            )
            
            # Déduire la mise
            try:
                wallet.debit(bet_amount, description=f'Mise Slots Game')
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
    def spin(self, request, pk=None):
        """Effectue une rotation des tambours"""
        try:
            game = self.get_object()
            
            if game.status != 'waiting':
                return Response({'error': 'Game not waiting'}, status=status.HTTP_400_BAD_REQUEST)
            
            result = game.spin()
            
            if 'error' in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
            # Si la partie est gagnée, transférer les gains
            if game.status == 'won':
                wallet, _ = Wallet.objects.get_or_create(utilisateur=game.player)
                wallet.credit(game.winnings, description=f'Gain Slots Game - {game.multiplier}x')
            
            return Response(result)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def my_games(self, request):
        """Récupère les parties de l'utilisateur"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        games = SlotsGame.objects.filter(player=user).order_by('-created_at')
        serializer = self.get_serializer(games, many=True)
        return Response(serializer.data)
