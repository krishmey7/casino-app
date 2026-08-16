from rest_framework import serializers
from .models import ScratchCardGame

class ScratchCardGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = ScratchCardGame
        fields = ['id', 'player_username', 'bet_amount', 'card_type', 'symbols', 'prize', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'symbols', 'prize', 'winnings', 'result', 'status', 'created_at', 'ended_at']