from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def fan_tan_game(request):
    return render(request, 'fan_tan/game.html')