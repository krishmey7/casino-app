from rest_framework import serializers
from .models import FaceOuPileGame


class FaceOuPileGameSerializer(serializers.ModelSerializer):
    player1 = serializers.CharField(source='player1.username', read_only=True)
    player2 = serializers.CharField(source='player2.username', allow_null=True, read_only=True)
    winner = serializers.CharField(source='winner.username', allow_null=True, read_only=True)
    result = serializers.SerializerMethodField()
    player2_choice = serializers.SerializerMethodField()  # Calculé dynamiquement
    opponent_choice = serializers.SerializerMethodField()  # Choix de l'adversaire pour la manche actuelle

    class Meta:
        model = FaceOuPileGame
        fields = [
            'id',
            'player1',
            'player2',
            'bet_amount',
            'chooser_choice',
            'player2_choice',
            'coin_result',
            'winner',
            'status',
            'created_at',
            'finished_at',
            'result',
            'player1_score',
            'player2_score',
            'current_round',
            'round_chooser',
            'round_results',
            'opponent_choice',
        ]
        read_only_fields = ['winner', 'status', 'finished_at', 'result', 'coin_result', 'player2_choice', 
                           'player1_score', 'player2_score', 'current_round', 'round_chooser', 'round_results', 'opponent_choice', 'chooser_choice']

    def get_player2_choice(self, obj):
        """Retourne le côté opposé du chooser (legacy pour compatibilité)"""
        if not obj.chooser_choice:
            return None
        return obj.get_opponent_choice(obj.chooser_choice)

    def get_opponent_choice(self, obj):
        """Retourne le choix de l'adversaire pour la manche actuelle"""
        if not obj.round_chooser or not obj.chooser_choice:
            return None
        return obj.get_opponent_choice(obj.chooser_choice)

    def get_result(self, obj):
        if not obj.coin_result:
            return None
        winner = obj.determine_round_winner()
        if winner == 'draw':
            return 'draw'
        return winner.username if winner else None
