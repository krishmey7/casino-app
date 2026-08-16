from rest_framework import serializers
from .models import SlotsGame


class SlotsGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = SlotsGame
        fields = ['id', 'player_username', 'status', 'bet_amount', 'multiplier', 'winnings',
                  'reel_1', 'reel_2', 'reel_3', 'created_at', 'ended_at']
        read_only_fields = ['id', 'status', 'multiplier', 'winnings', 'created_at', 'ended_at', 'reel_1', 'reel_2', 'reel_3']
