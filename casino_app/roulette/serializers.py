from rest_framework import serializers
from .models import RoulettePartie


class RoulettePartieSerializer(serializers.ModelSerializer):
    joueur_nom = serializers.CharField(source='joueur.username', read_only=True)

    class Meta:
        model = RoulettePartie
        fields = ['id', 'joueur_nom', 'statut', 'mise', 'numero_pari', 'numero_tire', 'gain', 'created_at', 'ended_at']
        read_only_fields = ['id', 'statut', 'numero_tire', 'gain', 'created_at', 'ended_at']
