from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def red_dog_game(request):
    return render(request, 'red_dog/game.html')