from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import MinesGame
from .serializers import MinesGameSerializer
from casino_app.wallet.models import Wallet


class MinesGameViewSet(viewsets.ModelViewSet):
    queryset = MinesGame.objects.all()
    serializer_class = MinesGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        """Crée et démarre une nouvelle partie"""
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            bet_amount = Decimal(str(request.data.get('bet_amount', '100.00')))
            mines_count = int(request.data.get('mines_count', 12))
            
            # Valider la mise
            if bet_amount <= 0:
                return Response({'error': 'Bet amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
            if mines_count < 1 or mines_count > 24:
                return Response({'error': 'Mines count must be between 1 and 24'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier le solde
            wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
            if wallet.balance < bet_amount:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer la partie
            game = MinesGame.objects.create(
                player=user,
                bet_amount=bet_amount,
                mines_count=mines_count
            )
            game.initialize_game(mines_count)
            
            # Déduire la mise
            try:
                wallet.debit(bet_amount, description=f'Mise Mines Game - {mines_count} mines')
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
    def reveal(self, request, pk=None):
        """Révèle une case"""
        try:
            game = self.get_object()
            
            if game.status != 'playing':
                return Response({'error': 'Game not playing'}, status=status.HTTP_400_BAD_REQUEST)
            
            cell_number = int(request.data.get('cell'))
            if cell_number < 0 or cell_number > 24:
                return Response({'error': 'Invalid cell number'}, status=status.HTTP_400_BAD_REQUEST)
            
            result = game.reveal_cell(cell_number)
            
            if 'error' in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(result)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def cashout(self, request, pk=None):
        """Encaisser les gains"""
        try:
            game = self.get_object()
            
            if game.status != 'playing':
                return Response({'error': 'Game not playing'}, status=status.HTTP_400_BAD_REQUEST)
            
            result = game.cash_out()
            
            if 'error' in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
            # Crédit des gains au portefeuille
            wallet, _ = Wallet.objects.get_or_create(utilisateur=game.player)
            wallet.credit(game.winnings, description=f'Gain Mines Game - {game.cells_revealed}x{game.current_multiplier}')
            
            serializer = self.get_serializer(game)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def my_games(self, request):
        """Récupère les parties de l'utilisateur"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        games = MinesGame.objects.filter(player=user).order_by('-created_at')
        serializer = self.get_serializer(games, many=True)
        return Response(serializer.data)
