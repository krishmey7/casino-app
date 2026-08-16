from rest_framework import serializers
from .models import CaribbeanStudPokerGame

class CaribbeanStudPokerGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = CaribbeanStudPokerGame
        fields = ['id', 'player_username', 'ante_bet', 'call_bet', 'player_cards', 'dealer_cards', 'player_hand_rank', 'dealer_hand_rank', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'player_cards', 'dealer_cards', 'player_hand_rank', 'dealer_hand_rank', 'winnings', 'result', 'status', 'created_at', 'ended_at']