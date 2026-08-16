from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from casino_app.wallet.models import Wallet


@login_required
def rock_paper_scissors_game(request):
    wallet, _ = Wallet.objects.get_or_create(utilisateur=request.user)
    return render(request, 'rock_paper_scissors/game.html', {
        'balance': wallet.balance,
        'user': request.user
    })