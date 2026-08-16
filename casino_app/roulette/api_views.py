from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from casino_app.roulette.models import RoulettePartie
from .serializers import RoulettePartieSerializer
from casino_app.wallet.models import Wallet


class RoulettePartieViewSet(viewsets.ModelViewSet):
    queryset = RoulettePartie.objects.all()
    serializer_class = RoulettePartieSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def demarrer(self, request):
        user = request.user
        mise = Decimal(str(request.data.get('mise', '100.00')))

        if mise <= 0:
            return Response({'error': 'La mise doit être positive'}, status=status.HTTP_400_BAD_REQUEST)

        wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
        if wallet.balance < mise:
            return Response({'error': 'Solde insuffisant'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wallet.debit(mise, description=f'Mise Roulette - {mise}')
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        partie = RoulettePartie.objects.create(joueur=user, mise=mise)
        serializer = self.get_serializer(partie)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def jouer(self, request, pk=None):
        partie = self.get_object()

        if partie.statut != 'en_cours':
            return Response({'error': 'La partie est terminée'}, status=status.HTTP_400_BAD_REQUEST)

        numero_pari = request.data.get('numero_pari')
        if numero_pari is None:
            return Response({'error': 'Le numéro pari est requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            numero_pari = int(numero_pari)
        except (ValueError, TypeError):
            return Response({'error': 'Numéro invalide'}, status=status.HTTP_400_BAD_REQUEST)

        result = partie.jouer(numero_pari)
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        if partie.statut == 'gagné':
            wallet, _ = Wallet.objects.get_or_create(utilisateur=partie.joueur)
            wallet.credit(partie.gain, description=f'Gain Roulette - partie {partie.id}')

        serializer = self.get_serializer(partie)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def mes_parties(self, request):
        user = request.user
        parties = RoulettePartie.objects.filter(joueur=user).order_by('-created_at')
        serializer = self.get_serializer(parties, many=True)
        return Response(serializer.data)
