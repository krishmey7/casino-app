from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def craps_game(request):
    """Vue pour afficher le jeu Craps"""
    return render(request, 'craps/game.html')