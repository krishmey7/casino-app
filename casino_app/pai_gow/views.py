from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def pai_gow_game(request):
    """Vue pour afficher le jeu Pai Gow"""
    return render(request, 'pai_gow/game.html')