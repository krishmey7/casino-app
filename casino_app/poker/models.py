from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random
import json
from collections import Counter


class PokerGame(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'En attente'),
        ('playing', 'En cours'),
        ('won', 'Gagné'),
        ('lost', 'Perdu'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='poker_games')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='playing')
    
    # Pari et gains
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('100.00'))
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    
    # Main de poker
    hand = models.JSONField(default=list)  # Liste de 5 cartes, e.g. ['AH', '2S', '3D', '4C', '5H']
    hold = models.JSONField(default=list)  # Liste des indices à garder [0,2,4]
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Poker Game {self.id} - {self.player.username} - {self.status}"

    def deal_hand(self):
        """Distribue une main initiale de 5 cartes"""
        deck = [rank + suit for rank in '23456789TJQKA' for suit in 'SHDC']
        random.shuffle(deck)
        self.hand = deck[:5]
        self.hold = []
        self.status = 'playing'
        self.save()

    def draw_cards(self, hold_indices):
        """Tire les cartes, gardant celles choisies"""
        self.hold = hold_indices
        deck = [rank + suit for rank in '23456789TJQKA' for suit in 'SHDC']
        # Remove already dealt cards to avoid duplicates, but for simplicity, reshuffle
        random.shuffle(deck)
        new_hand = self.hand[:]
        for i in range(5):
            if i not in hold_indices:
                new_hand[i] = deck.pop()
        self.hand = new_hand
        self.evaluate_hand()

    def evaluate_hand(self):
        """Évalue la main et calcule les gains"""
        def get_rank(card):
            ranks = '23456789TJQKA'
            return ranks.index(card[0])

        def get_suit(card):
            return card[1]

        ranks = sorted([get_rank(c) for c in self.hand])
        suits = [get_suit(c) for c in self.hand]

        # Flush
        is_flush = len(set(suits)) == 1

        # Straight
        is_straight = ranks == list(range(min(ranks), min(ranks)+5)) or ranks == [0,1,2,3,12]  # Ace low

        rank_counts = Counter(ranks)
        counts = sorted(rank_counts.values(), reverse=True)

        if is_straight and is_flush:
            if max(ranks) == 12:  # Royal flush
                multiplier = 100
            else:
                multiplier = 50  # Straight flush
        elif counts == [4,1]:
            multiplier = 25  # Four of a kind
        elif counts == [3,2]:
            multiplier = 9  # Full house
        elif is_flush:
            multiplier = 6  # Flush
        elif is_straight:
            multiplier = 4  # Straight
        elif counts == [3,1,1]:
            multiplier = 3  # Three of a kind
        elif counts == [2,2,1]:
            multiplier = 2  # Two pair
        elif counts == [2,1,1,1]:
            multiplier = 1  # One pair
        else:
            multiplier = 0  # Nothing

        self.winnings = self.bet_amount * multiplier
        if multiplier > 0:
            self.status = 'won'
        else:
            self.status = 'lost'
        self.ended_at = timezone.now()
        self.save()

    def cash_out(self):
        """Encaisser (mais pour poker, c'est automatique après draw)"""
        return {'winnings': float(self.winnings)}
#<parameter name="filePath">c:\Users\pc\Desktop\projet casino_045716\projet_casino\projet_casino\casino_app\poker\models.py