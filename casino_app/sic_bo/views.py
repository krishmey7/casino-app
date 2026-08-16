from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def sic_bo_game(request):
    """Vue pour afficher le jeu Sic Bo"""
    return render(request, 'sic_bo/game.html')