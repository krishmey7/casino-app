from rest_framework import serializers
from .models import BlackjackGame


class BlackjackGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = BlackjackGame
        fields = ['id', 'player_username', 'status', 'bet_amount', 'player_score', 'dealer_score',
                  'multiplier', 'winnings', 'player_cards', 'dealer_cards', 'created_at', 'ended_at']
        read_only_fields = ['id', 'status', 'player_score', 'dealer_score', 'multiplier', 'winnings', 
                           'created_at', 'ended_at', 'player_cards', 'dealer_cards']
