from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random


class RoulettePartie(models.Model):
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('gagné', 'Gagné'),
        ('perdu', 'Perdu'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    joueur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='roulette_parties')
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='en_cours')
    mise = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    numero_pari = models.IntegerField(null=True, blank=True)
    numero_tire = models.IntegerField(null=True, blank=True)
    gain = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Roulette Partie {self.id} - {self.joueur.username} - {self.statut}"

    def jouer(self, numero_pari):
        if self.statut != 'en_cours':
            return {'error': 'La partie est déjà terminée'}

        if numero_pari < 0 or numero_pari > 36:
            return {'error': 'Le numéro doit être entre 0 et 36'}

        self.numero_pari = numero_pari
        self.numero_tire = random.randint(0, 36)

        if self.numero_tire == self.numero_pari:
            self.gain = self.mise * Decimal('35.00')
            self.statut = 'gagné'
        else:
            self.gain = Decimal('0.00')
            self.statut = 'perdu'

        self.ended_at = timezone.now()
        self.save()

        return {
            'numero_pari': self.numero_pari,
            'numero_tire': self.numero_tire,
            'statut': self.statut,
            'gain': float(self.gain),
        }
