from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Wallet
from .serializers import WalletActionSerializer

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def balance_api(request):
    """Récupère le solde du portefeuille de l'utilisateur"""
    user = request.user
    wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
    return Response({'balance': str(wallet.balance), 'utilisateur': user.username})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def credit_api(request):
    serializer = WalletActionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    username = serializer.validated_data.get('username') or request.user.username
    amount = serializer.validated_data['amount']

    if username != request.user.username and not request.user.is_staff:
        return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    user = get_object_or_404(User, username=username)
    wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
    try:
        balance, tx = wallet.credit(amount, description=f'API credit by {request.user.username}')
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'balance': str(balance), 'tx_id': tx.id})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def debit_api(request):
    serializer = WalletActionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    username = serializer.validated_data.get('username') or request.user.username
    amount = serializer.validated_data['amount']

    if username != request.user.username and not request.user.is_staff:
        return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    user = get_object_or_404(User, username=username)
    wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
    try:
        balance, tx = wallet.debit(amount, description=f'API debit by {request.user.username}')
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'balance': str(balance), 'tx_id': tx.id})