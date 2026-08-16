from rest_framework import serializers
from .models import LetItRideGame

class LetItRideGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = LetItRideGame
        fields = ['id', 'player_username', 'bet_amount', 'side_bet', 'player_cards', 'community_cards', 'final_hand', 'hand_rank', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'player_cards', 'community_cards', 'final_hand', 'hand_rank', 'winnings', 'result', 'status', 'created_at', 'ended_at']