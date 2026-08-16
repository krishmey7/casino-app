from rest_framework import serializers
from .models import VideoPokerGame

class VideoPokerGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = VideoPokerGame
        fields = ['id', 'player_username', 'bet_amount', 'initial_cards', 'final_cards', 'hand_rank', 'payout_multiplier', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'initial_cards', 'final_cards', 'hand_rank', 'payout_multiplier', 'winnings', 'result', 'status', 'created_at', 'ended_at']