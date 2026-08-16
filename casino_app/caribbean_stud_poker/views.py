from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def caribbean_stud_poker_game(request):
    return render(request, 'caribbean_stud_poker/game.html')