from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from casino_app.wallet.models import Wallet


@login_required
def face_ou_pile_game(request):
    wallet, _ = Wallet.objects.get_or_create(utilisateur=request.user)
    return render(request, 'face_ou_pile/game.html', {
        'balance': wallet.balance,
        'user': request.user
    })
