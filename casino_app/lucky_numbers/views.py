from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def lucky_numbers_game(request):
    """Vue pour afficher le jeu de tirage de chiffres"""
    return render(request, 'lucky_numbers/game.html')
