from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def double_exposure_blackjack_game(request):
    return render(request, 'double_exposure_blackjack/game.html')