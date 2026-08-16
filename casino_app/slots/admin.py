from django.contrib import admin
from .models import SlotsGame


@admin.register(SlotsGame)
class SlotsGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'status', 'bet_amount', 'multiplier', 'winnings', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['player__username', 'id']
