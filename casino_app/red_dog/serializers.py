from rest_framework import serializers
from .models import RedDogGame

class RedDogGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = RedDogGame
        fields = ['id', 'player_username', 'bet_amount', 'bet_type', 'cards', 'spread', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'cards', 'spread', 'winnings', 'result', 'status', 'created_at', 'ended_at']