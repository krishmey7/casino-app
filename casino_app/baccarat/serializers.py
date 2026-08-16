from rest_framework import serializers
from .models import BaccaratGame

class BaccaratGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = BaccaratGame
        fields = ['id', 'player_username', 'bet_amount', 'bet_on', 'player_hand', 'banker_hand', 'result', 'winnings', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'player_hand', 'banker_hand', 'result', 'winnings', 'status', 'created_at', 'ended_at']