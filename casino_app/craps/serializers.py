from rest_framework import serializers
from .models import CrapsGame

class CrapsGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = CrapsGame
        fields = ['id', 'player_username', 'bet_amount', 'bet_type', 'dice_roll', 'point', 'result', 'winnings', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'dice_roll', 'result', 'winnings', 'status', 'created_at', 'ended_at']