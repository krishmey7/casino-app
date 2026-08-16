from django.contrib import admin
from .models import PaiGowGame

@admin.register(PaiGowGame)
class PaiGowGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_amount', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'created_at']
    search_fields = ['player__username', 'id']