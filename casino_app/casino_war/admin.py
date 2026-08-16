from django.contrib import admin
from .models import CasinoWarGame

@admin.register(CasinoWarGame)
class CasinoWarGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_amount', 'player_card', 'dealer_card', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'created_at']
    search_fields = ['player__username', 'id']