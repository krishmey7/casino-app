from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def pontoon_game(request):
    return render(request, 'pontoon/game.html')