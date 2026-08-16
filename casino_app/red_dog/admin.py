from django.contrib import admin
from .models import RedDogGame

@admin.register(RedDogGame)
class RedDogGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_type', 'bet_amount', 'spread', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'bet_type', 'created_at']
    search_fields = ['player__username', 'id']