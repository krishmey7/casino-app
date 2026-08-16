from django.contrib import admin
from .models import DoubleExposureBlackjackGame

@admin.register(DoubleExposureBlackjackGame)
class DoubleExposureBlackjackGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_amount', 'player_score', 'dealer_score', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'created_at']
    search_fields = ['player__username', 'id']