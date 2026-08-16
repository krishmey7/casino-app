from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def mines_game(request):
    """Vue pour afficher le jeu Mines"""
    return render(request, 'golitep/game.html')
