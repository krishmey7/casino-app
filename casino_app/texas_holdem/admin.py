from django.contrib import admin
from .models import TexasHoldemGame

@admin.register(TexasHoldemGame)
class TexasHoldemGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_amount', 'hand_rank', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'hand_rank', 'created_at']
    search_fields = ['player__username', 'id']