from django.contrib import admin
from .models import LetItRideGame

@admin.register(LetItRideGame)
class LetItRideGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_amount', 'side_bet', 'hand_rank', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'hand_rank', 'created_at']
    search_fields = ['player__username', 'id']