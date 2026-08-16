from rest_framework import serializers
from .models import PontoonGame

class PontoonGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = PontoonGame
        fields = ['id', 'player_username', 'bet_amount', 'player_cards', 'dealer_cards', 'player_score', 'dealer_score', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'player_cards', 'dealer_cards', 'player_score', 'dealer_score', 'winnings', 'result', 'status', 'created_at', 'ended_at']