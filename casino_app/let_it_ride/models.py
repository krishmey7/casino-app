from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class LetItRideGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='let_it_ride_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50.00'))
    side_bet = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    player_cards = models.JSONField(default=list)
    community_cards = models.JSONField(default=list)
    
    final_hand = models.JSONField(default=list)
    hand_rank = models.CharField(max_length=20, null=True, blank=True)
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    result = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, default='finished')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Let It Ride Game {self.id} - {self.player.username}"

    def get_hand_rank(self, cards):
        """Détermine le rang de la main poker"""
        ranks = [card % 13 for card in cards]
        suits = [card // 13 for card in cards]
        
        # Compter les occurrences de chaque rang
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        # Vérifier les combinaisons
        counts = sorted(rank_counts.values(), reverse=True)
        
        # Royal flush
        if len(set(suits)) == 1 and sorted(ranks) == [0, 9, 10, 11, 12]:
            return 'royal_flush'
        
        # Straight flush
        if len(set(suits)) == 1:
            sorted_ranks = sorted(ranks)
            if sorted_ranks == [0, 1, 2, 3, 12]:  # As-2-3-4-5
                return 'straight_flush'
            elif sorted_ranks[4] - sorted_ranks[0] == 4:
                return 'straight_flush'
        
        # Four of a kind
        if counts[0] == 4:
            return 'four_of_a_kind'
        
        # Full house
        if counts == [3, 2]:
            return 'full_house'
        
        # Flush
        if len(set(suits)) == 1:
            return 'flush'
        
        # Straight
        sorted_ranks = sorted(ranks)
        if sorted_ranks == [0, 1, 2, 3, 12]:  # As-2-3-4-5
            return 'straight'
        elif sorted_ranks[4] - sorted_ranks[0] == 4:
            return 'straight'
        
        # Three of a kind
        if counts[0] == 3:
            return 'three_of_a_kind'
        
        # Two pair
        if counts == [2, 2, 1]:
            return 'two_pair'
        
        # One pair
        if counts[0] == 2:
            return 'one_pair'
        
        return 'high_card'

    def play_game(self):
        """Lance le jeu Let It Ride"""
        # Tire 6 cartes
        deck = list(range(1, 53))
        all_cards = random.sample(deck, 6)
        self.player_cards = all_cards[:3]
        self.community_cards = all_cards[3:]
        
        # Main finale = 3 cartes joueur + 2 cartes communauté
        self.final_hand = self.player_cards + self.community_cards[:2]
        self.hand_rank = self.get_hand_rank(self.final_hand)
        
        # Calcul des gains selon la main
        payouts = {
            'royal_flush': 1000,
            'straight_flush': 200,
            'four_of_a_kind': 50,
            'full_house': 11,
            'flush': 8,
            'straight': 5,
            'three_of_a_kind': 3,
            'two_pair': 2,
            'one_pair': 1,
            'high_card': 1
        }
        
        multiplier = payouts.get(self.hand_rank, 1)
        self.winnings = self.bet_amount * multiplier
        
        # Side bet bonus pour paires et mieux
        if self.side_bet > 0:
            side_payouts = {
                'royal_flush': 10000,
                'straight_flush': 1000,
                'four_of_a_kind': 100,
                'full_house': 50,
                'flush': 25,
                'straight': 10,
                'three_of_a_kind': 5,
                'two_pair': 2,
                'one_pair': 1
            }
            side_multiplier = side_payouts.get(self.hand_rank, 0)
            self.winnings += self.side_bet * side_multiplier
        
        self.result = 'win' if self.winnings > 0 else 'lose'
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()