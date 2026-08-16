from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def keno_game(request):
    """Vue pour afficher le jeu Keno"""
    return render(request, 'keno/game.html')