from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def baccarat_game(request):
    """Vue pour afficher le jeu Baccarat"""
    return render(request, 'baccarat/game.html')