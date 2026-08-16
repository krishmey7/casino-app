from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def poker_game(request):
    """Vue pour afficher le jeu Poker"""
    return render(request, 'poker/game.html')