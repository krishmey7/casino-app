from rest_framework import serializers
from .models import SicBoGame

class SicBoGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = SicBoGame
        fields = ['id', 'player_username', 'bet_amount', 'bet_type', 'dice', 'total', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'dice', 'total', 'winnings', 'result', 'status', 'created_at', 'ended_at']