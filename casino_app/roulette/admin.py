from django.contrib import admin
from .models import RoulettePartie


@admin.register(RoulettePartie)
class RoulettePartieAdmin(admin.ModelAdmin):
    list_display = ['id', 'joueur', 'statut', 'mise', 'numero_pari', 'numero_tire', 'gain', 'created_at', 'ended_at']
    list_filter = ['statut']
    readonly_fields = ['created_at', 'ended_at']
