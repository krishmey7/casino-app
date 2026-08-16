from rest_framework import serializers
from .models import RockPaperScissorsGame


class RockPaperScissorsGameSerializer(serializers.ModelSerializer):
    player1 = serializers.CharField(source='player1.username', read_only=True)
    player2 = serializers.CharField(source='player2.username', allow_null=True, read_only=True)
    winner = serializers.CharField(source='winner.username', allow_null=True, read_only=True)
    result = serializers.SerializerMethodField()
    player1_has_chosen = serializers.SerializerMethodField()
    player2_has_chosen = serializers.SerializerMethodField()
    both_chosen = serializers.SerializerMethodField()

    class Meta:
        model = RockPaperScissorsGame
        fields = [
            'id',
            'player1',
            'player2',
            'bet_amount',
            'player1_choice',
            'player2_choice',
            'player1_has_chosen',
            'player2_has_chosen',
            'both_chosen',
            'winner',
            'status',
            'created_at',
            'finished_at',
            'result'
        ]
        read_only_fields = ['winner', 'status', 'finished_at', 'result', 'player1_has_chosen', 'player2_has_chosen', 'both_chosen']

    def get_player1_has_chosen(self, obj):
        return bool(obj.player1_choice)

    def get_player2_has_chosen(self, obj):
        return bool(obj.player2_choice)

    def get_both_chosen(self, obj):
        return bool(obj.player1_choice and obj.player2_choice)

    def get_result(self, obj):
        if not obj.player1_choice or not obj.player2_choice:
            return None

        winner = obj.determine_winner()
        if winner == 'draw':
            return 'draw'
        return winner.username if winner else None

    def to_representation(self, instance):
        # Masquer les choix réels tant que les deux joueurs n'ont pas choisi
        data = super().to_representation(instance)
        
        # Si la partie n'est pas terminée, masquer les choix
        if instance.status != 'finished':
            data['player1_choice'] = None
            data['player2_choice'] = None
        
        return data