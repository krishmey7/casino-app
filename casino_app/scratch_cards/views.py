from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def scratch_cards_game(request):
    return render(request, 'scratch_cards/game.html')