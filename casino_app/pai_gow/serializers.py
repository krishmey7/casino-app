from rest_framework import serializers
from .models import PaiGowGame

class PaiGowGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = PaiGowGame
        fields = ['id', 'player_username', 'bet_amount', 'player_tiles', 'banker_tiles', 'player_high', 'player_low', 'banker_high', 'banker_low', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'player_tiles', 'banker_tiles', 'player_high', 'player_low', 'banker_high', 'banker_low', 'winnings', 'result', 'status', 'created_at', 'ended_at']