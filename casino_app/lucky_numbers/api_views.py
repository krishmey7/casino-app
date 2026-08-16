from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from .models import LuckyNumberGame, LuckyNumberBet
from .serializers import LuckyNumberGameSerializer, LuckyNumberBetSerializer
from casino_app.wallet.models import Wallet


class LuckyNumberGameViewSet(viewsets.ModelViewSet):
    queryset = LuckyNumberGame.objects.all()
    serializer_class = LuckyNumberGameSerializer

    @action(detail=False, methods=['post'])
    def start_new_game(self, request):
        """Crée et démarre une nouvelle partie"""
        game = LuckyNumberGame.objects.create()
        game.start_game()
        serializer = self.get_serializer(game)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def draw(self, request, pk=None):
        """Effectue le tirage aléatoire"""
        game = self.get_object()
        if game.status != 'playing':
            return Response({'error': 'Game not in playing status'}, status=status.HTTP_400_BAD_REQUEST)
        
        game.finish_game()
        
        # Vérifier les résultats de tous les paris de cette partie
        for bet in game.bets.filter(status='pending'):
            bet.check_result()
            # Mettre à jour le portefeuille avec les bons appels
            wallet, _ = Wallet.objects.get_or_create(utilisateur=bet.player)
            if bet.status == 'won':
                # Crédit du gain
                wallet.credit(bet.winnings, description=f'Gain Lucky Number Game - Numéro {bet.chosen_number}')
            # Note: la mise est déjà déduite lors du placement du pari
        
        serializer = self.get_serializer(game)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Récupère la partie actuelle ou en crée une"""
        game = LuckyNumberGame.objects.filter(status='playing').first()
        if not game:
            game = LuckyNumberGame.objects.create()
            game.start_game()
        
        serializer = self.get_serializer(game)
        return Response(serializer.data)


class LuckyNumberBetViewSet(viewsets.ModelViewSet):
    queryset = LuckyNumberBet.objects.all()
    serializer_class = LuckyNumberBetSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Créer un nouveau pari"""
        user = request.user
        game_id = request.data.get('game')
        chosen_number = request.data.get('chosen_number')
        bet_amount = Decimal(request.data.get('bet_amount', '100.00'))

        # Valider le numéro choisi
        if chosen_number is None or chosen_number < 0 or chosen_number > 9:
            return Response({'error': 'Number must be between 0 and 9'}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier que l'utilisateur a assez d'argent
        wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
        if wallet.balance < bet_amount:
            return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

        # Récupérer ou créer la partie
        try:
            game = LuckyNumberGame.objects.get(id=game_id)
        except LuckyNumberGame.DoesNotExist:
            game = LuckyNumberGame.objects.create()
            game.start_game()

        if game.status != 'playing':
            return Response({'error': 'Game not available'}, status=status.HTTP_400_BAD_REQUEST)

        # Créer le pari
        bet = LuckyNumberBet.objects.create(
            game=game,
            player=user,
            chosen_number=chosen_number,
            bet_amount=bet_amount
        )

        # Déduire la mise du portefeuille avec la méthode debit
        try:
            wallet.debit(bet_amount, description=f'Mise Lucky Number Game - Chiffre choisi: {chosen_number}')
        except ValueError as e:
            bet.delete()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(bet)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def my_bets(self, request):
        """Récupère les paris de l'utilisateur connecté"""
        user = request.user
        bets = LuckyNumberBet.objects.filter(player=user).order_by('-bet_time')
        serializer = self.get_serializer(bets, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def game_bets(self, request):
        """Récupère les paris d'une partie spécifique"""
        game_id = request.query_params.get('game_id')
        if not game_id:
            return Response({'error': 'game_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        bets = LuckyNumberBet.objects.filter(game_id=game_id)
        serializer = self.get_serializer(bets, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_bets(self, request):
        """Récupère les paris de l'utilisateur connecté"""
        user = request.user
        bets = LuckyNumberBet.objects.filter(player=user).order_by('-bet_time')
        serializer = self.get_serializer(bets, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def game_bets(self, request):
        """Récupère les paris d'une partie spécifique"""
        game_id = request.query_params.get('game_id')
        if not game_id:
            return Response({'error': 'game_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        bets = LuckyNumberBet.objects.filter(game_id=game_id)
        serializer = self.get_serializer(bets, many=True)
        return Response(serializer.data)
