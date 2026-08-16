from django.contrib import admin
from .models import SicBoGame

@admin.register(SicBoGame)
class SicBoGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_type', 'bet_amount', 'total', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'bet_type', 'created_at']
    search_fields = ['player__username', 'id']