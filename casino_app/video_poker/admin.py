from django.contrib import admin
from .models import VideoPokerGame

@admin.register(VideoPokerGame)
class VideoPokerGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_amount', 'hand_rank', 'payout_multiplier', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'hand_rank', 'created_at']
    search_fields = ['player__username', 'id']