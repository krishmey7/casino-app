from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def spanish_21_game(request):
    return render(request, 'spanish_21/game.html')