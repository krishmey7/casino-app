from django.contrib import admin
from .models import LuckyNumberGame, LuckyNumberBet


@admin.register(LuckyNumberGame)
class LuckyNumberGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'winning_number', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id']


@admin.register(LuckyNumberBet)
class LuckyNumberBetAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'game', 'chosen_number', 'bet_amount', 'status', 'winnings']
    list_filter = ['status', 'bet_time']
    search_fields = ['player__username', 'game__id']
