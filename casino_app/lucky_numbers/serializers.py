from rest_framework import serializers
from .models import LuckyNumberGame, LuckyNumberBet


class LuckyNumberGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = LuckyNumberGame
        fields = ['id', 'status', 'winning_number', 'created_at', 'finished_at']


class LuckyNumberBetSerializer(serializers.ModelSerializer):
    player_username = serializers.CharField(source='player.username', read_only=True)

    class Meta:
        model = LuckyNumberBet
        fields = ['id', 'game', 'player_username', 'chosen_number', 'bet_amount', 'status', 'winnings', 'bet_time', 'result_time']
        read_only_fields = ['id', 'status', 'winnings', 'bet_time', 'result_time']
