from rest_framework import serializers
from .models import MinesGame


class MinesGameSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)
    
    class Meta:
        model = MinesGame
        fields = ['id', 'player_username', 'status', 'difficulty', 'bet_amount', 'current_multiplier', 
                  'winnings', 'cells_revealed', 'mines_count', 'created_at', 'ended_at', 'revealed', 'grid']
        read_only_fields = ['id', 'status', 'winnings', 'created_at', 'ended_at', 'revealed', 'grid']
