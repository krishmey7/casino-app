from django.contrib import admin
from .models import RockPaperScissorsGame

@admin.register(RockPaperScissorsGame)
class RockPaperScissorsGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player1', 'player2', 'bet_amount', 'status', 'winner']
    readonly_fields = ['created_at', 'finished_at']