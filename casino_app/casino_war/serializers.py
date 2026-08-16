from rest_framework import serializers
from .models import CasinoWarGame

class CasinoWarGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = CasinoWarGame
        fields = ['id', 'player_username', 'bet_amount', 'player_card', 'dealer_card', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'player_card', 'dealer_card', 'winnings', 'result', 'status', 'created_at', 'ended_at']