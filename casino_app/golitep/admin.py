from django.contrib import admin
from .models import MinesGame


@admin.register(MinesGame)
class MinesGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'status', 'bet_amount', 'current_multiplier', 'cells_revealed', 'mines_count', 'created_at']
    list_filter = ['status', 'difficulty', 'created_at']
    search_fields = ['player__username', 'id']
