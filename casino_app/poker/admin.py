from django.contrib import admin
from .models import PokerGame


@admin.register(PokerGame)
class PokerGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'status', 'bet_amount', 'winnings', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['player__username', 'id']