from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def video_poker_game(request):
    return render(request, 'video_poker/game.html')