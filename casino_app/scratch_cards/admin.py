from django.contrib import admin
from .models import ScratchCardGame

@admin.register(ScratchCardGame)
class ScratchCardGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_amount', 'card_type', 'prize', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'card_type', 'created_at']
    search_fields = ['player__username', 'id']