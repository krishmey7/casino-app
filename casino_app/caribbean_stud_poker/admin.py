from django.contrib import admin
from .models import CaribbeanStudPokerGame

@admin.register(CaribbeanStudPokerGame)
class CaribbeanStudPokerGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'ante_bet', 'call_bet', 'player_hand_rank', 'dealer_hand_rank', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'player_hand_rank', 'dealer_hand_rank', 'created_at']
    search_fields = ['player__username', 'id']