from rest_framework import serializers
from .models import FanTanGame

class FanTanGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = FanTanGame
        fields = ['id', 'player_username', 'bet_amount', 'bet_type', 'cards', 'remainder', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'cards', 'remainder', 'winnings', 'result', 'status', 'created_at', 'ended_at']