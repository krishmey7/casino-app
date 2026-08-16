from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def casino_war_game(request):
    return render(request, 'casino_war/game.html')