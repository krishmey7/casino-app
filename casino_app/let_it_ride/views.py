from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def let_it_ride_game(request):
    return render(request, 'let_it_ride/game.html')