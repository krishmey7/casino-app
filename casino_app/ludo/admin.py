from django.contrib import admin
from .models import LudoGame, LudoPlayer, LudoGameTransaction


@admin.register(LudoGame)
class LudoGameAdmin(admin.ModelAdmin):
    """Admin pour les parties LUDO"""
    list_display = ['id', 'status', 'current_turn', 'stake', 'winner', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'winner__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'started_at', 'finished_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'status', 'stake', 'current_turn', 'winner')
        }),
        ('État du jeu', {
            'fields': ('game_state',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'started_at', 'finished_at')
        }),
    )


@admin.register(LudoPlayer)
class LudoPlayerAdmin(admin.ModelAdmin):
    """Admin pour les joueurs LUDO"""
    list_display = ['user', 'game', 'color', 'turn_order', 'is_connected', 'is_ready', 'joined_at']
    list_filter = ['color', 'is_connected', 'is_ready', 'joined_at']
    search_fields = ['user__username', 'game__id']
    readonly_fields = ['joined_at', 'last_activity']
    
    fieldsets = (
        ('Informations du joueur', {
            'fields': ('game', 'user', 'color', 'turn_order')
        }),
        ('État du joueur', {
            'fields': ('is_connected', 'is_ready', 'remaining_time')
        }),
        ('Timestamps', {
            'fields': ('joined_at', 'last_activity')
        }),
    )


@admin.register(LudoGameTransaction)
class LudoGameTransactionAdmin(admin.ModelAdmin):
    """Admin pour les transactions LUDO"""
    list_display = ['game', 'user', 'transaction_type', 'amount', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['game__id', 'user__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Informations de la transaction', {
            'fields': ('game', 'user', 'transaction_type', 'amount')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
