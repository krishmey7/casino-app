from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import BlackjackGame
from .serializers import BlackjackGameSerializer
from casino_app.wallet.models import Wallet


class BlackjackGameViewSet(viewsets.ModelViewSet):
    queryset = BlackjackGame.objects.all()
    serializer_class = BlackjackGameSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        """Crée et démarre une nouvelle partie de blackjack"""
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
            game = BlackjackGame.objects.create(
                player=user,
                bet_amount=bet_amount
            )
            game.initialize_game()
            
            # Déduire la mise
            try:
                wallet.debit(bet_amount, description=f'Mise Blackjack Game')
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
    def hit(self, request, pk=None):
        """Tire une carte supplémentaire"""
        try:
            game = self.get_object()
            
            if game.status != 'playing':
                return Response({'error': 'Game not playing'}, status=status.HTTP_400_BAD_REQUEST)
            
            result = game.hit()
            
            if 'error' in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
            # Si le joueur a fait bust, ajouter les gains au portefeuille (zéro)
            if game.status == 'busted':
                wallet, _ = Wallet.objects.get_or_create(utilisateur=game.player)
                # Pas de crédit de gains si bust
            
            return Response(result)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def stand(self, request, pk=None):
        """Le joueur s'arrête et le croupier joue"""
        try:
            game = self.get_object()
            
            if game.status != 'playing':
                return Response({'error': 'Game not playing'}, status=status.HTTP_400_BAD_REQUEST)
            
            result = game.stand()
            
            if 'error' in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
            # Transférer les gains au portefeuille
            if game.status in ['won', 'push']:
                wallet, _ = Wallet.objects.get_or_create(utilisateur=game.player)
                if game.winnings > 0:
                    wallet.credit(game.winnings, description=f'Gain Blackjack Game - {game.multiplier}x')
                elif game.status == 'push':
                    wallet.credit(game.bet_amount, description=f'Remboursement Blackjack Game (égalité)')
            
            return Response(result)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def my_games(self, request):
        """Récupère les parties de l'utilisateur"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        games = BlackjackGame.objects.filter(player=user).order_by('-created_at')
        serializer = self.get_serializer(games, many=True)
        return Response(serializer.data)
