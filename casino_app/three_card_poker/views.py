from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def three_card_poker_game(request):
    return render(request, 'three_card_poker/game.html')