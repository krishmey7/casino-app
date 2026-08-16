from django.contrib import admin
from .models import BaccaratGame

@admin.register(BaccaratGame)
class BaccaratGameAdmin(admin.ModelAdmin):
    list_display = ['id', 'player', 'bet_on', 'bet_amount', 'result', 'winnings', 'created_at']
    list_filter = ['result', 'bet_on', 'created_at']
    search_fields = ['player__username', 'id']