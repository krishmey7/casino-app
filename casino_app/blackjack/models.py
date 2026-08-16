from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random
import json


class BlackjackGame(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'En attente'),
        ('playing', 'En cours'),
        ('stood', 'Debout'),
        ('busted', 'Dépassé'),
        ('won', 'Gagné'),
        ('lost', 'Perdu'),
        ('push', 'Égalité'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blackjack_games')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='playing')
    
    # Cartes (stockées comme JSON: list de dicts)
    player_cards = models.JSONField(default=list)  # Cartes du joueur
    dealer_cards = models.JSONField(default=list)  # Cartes du croupier
    
    # Pari et gains
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    multiplier = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    
    # Scores
    player_score = models.IntegerField(default=0)
    dealer_score = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Blackjack Game {self.id} - {self.player.username} - {self.status}"

    def initialize_game(self):
        """Initialise une nouvelle partie de blackjack"""
        # Créer un deck et distribuer 2 cartes à chaque
        deck = self._create_deck()
        self.player_cards = [self._draw_card(deck), self._draw_card(deck)]
        self.dealer_cards = [self._draw_card(deck), self._draw_card(deck)]
        self.player_score = self._calculate_score(self.player_cards)
        self.dealer_score = self._calculate_score(self.dealer_cards)  # Basé sur les 2 cartes!
        self.status = 'playing'
        self.save()
        
        # Vérifier blackjack du joueur
        if self.player_score == 21:
            self.status = 'won'
            self.multiplier = Decimal('2.50')  # Blackjack = 2.5x
            self.winnings = self.bet_amount * self.multiplier
            self.ended_at = timezone.now()
            self.save()

    def hit(self):
        """Tirer une carte supplémentaire"""
        if self.status != 'playing':
            return {'error': 'Game not playing'}
        
        deck = self._create_deck()
        new_card = self._draw_card(deck)
        self.player_cards.append(new_card)
        self.player_score = self._calculate_score(self.player_cards)
        
        if self.player_score > 21:
            self.status = 'busted'
            self.multiplier = Decimal('0.00')
            self.winnings = Decimal('0.00')
            self.ended_at = timezone.now()
        
        self.save()
        return {
            'player_score': self.player_score,
            'player_cards': self.player_cards,
            'status': self.status
        }

    def stand(self):
        """Le joueur s'arrête"""
        if self.status != 'playing':
            return {'error': 'Game not playing'}
        
        self.status = 'stood'
        
        # Croupier joue automatiquement jusqu'à 17+
        deck = self._create_deck()
        while self.dealer_score < 17:
            self.dealer_cards.append(self._draw_card(deck))
            self.dealer_score = self._calculate_score(self.dealer_cards)
        
        # Déterminer le résultat
        if self.dealer_score > 21:
            self.status = 'won'
            self.multiplier = Decimal('2.00')
        elif self.dealer_score > self.player_score:
            self.status = 'lost'
            self.multiplier = Decimal('0.00')
        elif self.dealer_score < self.player_score:
            self.status = 'won'
            self.multiplier = Decimal('2.00')
        else:
            self.status = 'push'
            self.multiplier = Decimal('1.00')
        
        if self.multiplier > Decimal('1.00'):
            self.winnings = self.bet_amount * self.multiplier
        else:
            self.winnings = Decimal('0.00')
        
        self.ended_at = timezone.now()
        self.save()
        
        return {
            'status': self.status,
            'dealer_score': self.dealer_score,
            'dealer_cards': self.dealer_cards,
            'multiplier': float(self.multiplier),
            'winnings': float(self.winnings)
        }

    def _create_deck(self):
        """Crée un deck de cartes standard"""
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = []
        for suit in suits:
            for rank in ranks:
                deck.append({'rank': rank, 'suit': suit})
        random.shuffle(deck)
        return deck

    def _draw_card(self, deck):
        """Tire une carte du deck"""
        if deck:
            return deck.pop()
        return None

    def _calculate_score(self, cards):
        """Calcule le score des cartes (blackjack rules)"""
        score = 0
        aces = 0
        
        for card in cards:
            if card is None:
                continue
            if card['rank'] == 'A':
                aces += 1
                score += 11
            elif card['rank'] in ['J', 'Q', 'K']:
                score += 10
            else:
                score += int(card['rank'])
        
        # Ajuster pour les as
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
        
        return score
