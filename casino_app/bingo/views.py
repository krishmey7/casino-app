from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def bingo_game(request):
    """Vue pour afficher le jeu Bingo"""
    return render(request, 'bingo/game.html')