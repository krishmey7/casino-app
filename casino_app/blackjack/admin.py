from django.contrib import admin
from .models import BlackjackGame


@admin.register(BlackjackGame)
class BlackjackGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'status', 'bet_amount', 'player_score', 'dealer_score', 'multiplier', 'winnings', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['player__username', 'id']
