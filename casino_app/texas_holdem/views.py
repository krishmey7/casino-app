from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def texas_holdem_game(request):
    return render(request, 'texas_holdem/game.html')