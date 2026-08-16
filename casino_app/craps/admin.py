from django.contrib import admin
from .models import CrapsGame

@admin.register(CrapsGame)
class CrapsGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_type', 'bet_amount', 'point', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'bet_type', 'created_at']
    search_fields = ['player__username', 'id']