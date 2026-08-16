from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .models import Wallet

User = get_user_model()


@login_required
def wallet_view(request):
    """Page principale du wallet avec design moderne"""
    wallet, _ = Wallet.objects.get_or_create(utilisateur=request.user)
    
    # Récupérer toutes les transactions (pour le déroulement)
    all_transactions = wallet.transactions.all().order_by('-date_transaction')
    # Afficher seulement 3 transactions par défaut
    transactions = all_transactions[:3]
    
    context = {
        'wallet': wallet,
        'transactions': transactions,
        'all_transactions': all_transactions,
        'balance': wallet.balance,
    }
    return render(request, 'wallet/wallet.html', context)


@require_GET
def balance_view(request):
    # Return current authenticated user's wallet balance as JSON
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    wallet, _ = Wallet.objects.get_or_create(utilisateur=request.user)
    return JsonResponse({'balance': str(wallet.balance)})


@require_POST
def credit_view(request):
    # Require authentication
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    username = request.POST.get('username') or request.user.username
    amount = request.POST.get('amount')
    if amount is None:
        return JsonResponse({'error': 'amount required'}, status=400)

    # Only staff can credit other users
    if username != request.user.username and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    user = get_object_or_404(User, username=username)
    wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
    try:
        balance, tx = wallet.credit(amount, description=f'API credit by {request.user.username}')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'balance': str(balance), 'tx_id': tx.id})


@require_POST
def debit_view(request):
    # Require authentication
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    username = request.POST.get('username') or request.user.username
    amount = request.POST.get('amount')
    if amount is None:
        return JsonResponse({'error': 'amount required'}, status=400)

    # Only staff can debit other users
    if username != request.user.username and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    user = get_object_or_404(User, username=username)
    wallet, _ = Wallet.objects.get_or_create(utilisateur=user)
    try:
        balance, tx = wallet.debit(amount, description=f'API debit by {request.user.username}')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'balance': str(balance), 'tx_id': tx.id})