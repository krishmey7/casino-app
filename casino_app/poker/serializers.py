from rest_framework import serializers
from .models import PokerGame


class PokerGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = PokerGame
        fields = ['id', 'player_username', 'status', 'bet_amount', 'winnings', 'hand', 'hold', 'created_at', 'ended_at']
        read_only_fields = ['id', 'status', 'winnings', 'hand', 'created_at', 'ended_at']