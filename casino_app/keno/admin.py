from django.contrib import admin
from .models import KenoGame

@admin.register(KenoGame)
class KenoGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_amount', 'matches', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'created_at']
    search_fields = ['player__username', 'id']