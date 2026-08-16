from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def omaha_poker_game(request):
    return render(request, 'omaha_poker/game.html')