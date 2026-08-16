from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from casino_app.wallet.models import Wallet


@login_required
def slots_game(request):
    wallet, _ = Wallet.objects.get_or_create(utilisateur=request.user)
    return render(request, 'slots/game.html', {'balance': wallet.balance})
