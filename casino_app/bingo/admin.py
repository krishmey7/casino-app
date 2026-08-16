from django.contrib import admin
from .models import BingoGame

@admin.register(BingoGame)
class BingoGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_amount', 'lines_complete', 'full_card', 'winnings', 'created_at']
    list_filter = ['full_card', 'created_at']
    search_fields = ['player__username', 'id']