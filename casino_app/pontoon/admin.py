from django.contrib import admin
from .models import PontoonGame

@admin.register(PontoonGame)
class PontoonGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_amount', 'player_score', 'dealer_score', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'created_at']
    search_fields = ['player__username', 'id']