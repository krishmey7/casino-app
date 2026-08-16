from rest_framework import serializers
from .models import TexasHoldemGame

class TexasHoldemGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = TexasHoldemGame
        fields = ['id', 'player_username', 'bet_amount', 'hole_cards', 'community_cards', 'best_hand', 'hand_rank', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'hole_cards', 'community_cards', 'best_hand', 'hand_rank', 'winnings', 'result', 'status', 'created_at', 'ended_at']