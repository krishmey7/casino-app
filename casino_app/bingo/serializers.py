from rest_framework import serializers
from .models import BingoGame

class BingoGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = BingoGame
        fields = ['id', 'player_username', 'bet_amount', 'card', 'drawn_numbers', 'lines_complete', 'column_complete', 'full_card', 'winnings', 'result', 'status', 'created_at', 'ended_at']
        read_only_fields = ['id', 'drawn_numbers', 'lines_complete', 'column_complete', 'full_card', 'winnings', 'result', 'status', 'created_at', 'ended_at']