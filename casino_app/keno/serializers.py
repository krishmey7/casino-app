from rest_framework import serializers
from .models import KenoGame

class KenoGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = KenoGame
        fields = ['id', 'player_username', 'bet_amount', 'picks', 'drawn_numbers', 'matches', 'payout_table', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'drawn_numbers', 'matches', 'payout_table', 'winnings', 'result', 'status', 'created_at', 'ended_at']