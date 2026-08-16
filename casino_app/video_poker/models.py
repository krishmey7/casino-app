from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class VideoPokerGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_poker_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50.00'))
    initial_cards = models.JSONField(default=list)  # 5 cartes initiales
    final_cards = models.JSONField(default=list)  # 5 cartes finales après échanges
    
    hand_rank = models.CharField(max_length=20, null=True, blank=True)
    payout_multiplier = models.IntegerField(default=0)
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    result = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, default='finished')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Video Poker Game {self.id} - {self.player.username}"

    def get_hand_rank(self, cards):
        """Détermine le rang de la main de poker"""
        if len(cards) != 5:
            return 'invalid'
        
        # Trier les cartes par rang
        sorted_cards = sorted(cards, key=lambda x: x % 13)
        ranks = [card % 13 for card in sorted_cards]
        suits = [card // 13 for card in sorted_cards]
        
        # Vérifier les combinaisons
        is_flush = len(set(suits)) == 1
        is_straight = self._is_straight(ranks)
        
        if is_flush and is_straight:
            if ranks == [0, 9, 10, 11, 12]:  # As-Roi-Dame-Valet-10
                return 'royal_flush'
            return 'straight_flush'
        elif self._has_four_of_a_kind(ranks):
            return 'four_of_a_kind'
        elif self._has_full_house(ranks):
            return 'full_house'
        elif is_flush:
            return 'flush'
        elif is_straight:
            return 'straight'
        elif self._has_three_of_a_kind(ranks):
            return 'three_of_a_kind'
        elif self._has_two_pairs(ranks):
            return 'two_pairs'
        elif self._has_pair(ranks):
            return 'pair'
        else:
            return 'high_card'

    def _is_straight(self, ranks):
        """Vérifie si c'est une suite"""
        unique_ranks = sorted(set(ranks))
        if len(unique_ranks) != 5:
            return False
        
        # Suite normale
        for i in range(4):
            if unique_ranks[i+1] - unique_ranks[i] != 1:
                break
        else:
            return True
        
        # Suite avec As (A-2-3-4-5)
        if unique_ranks == [0, 1, 2, 3, 12]:
            return True
        
        return False

    def _has_four_of_a_kind(self, ranks):
        return any(ranks.count(rank) == 4 for rank in set(ranks))

    def _has_full_house(self, ranks):
        rank_counts = [ranks.count(rank) for rank in set(ranks)]
        return sorted(rank_counts) == [2, 3]

    def _has_three_of_a_kind(self, ranks):
        return any(ranks.count(rank) == 3 for rank in set(ranks))

    def _has_two_pairs(self, ranks):
        rank_counts = [ranks.count(rank) for rank in set(ranks)]
        return rank_counts.count(2) == 2

    def _has_pair(self, ranks):
        return any(ranks.count(rank) == 2 for rank in set(ranks))

    def get_payout_multiplier(self, hand_rank):
        """Retourne le multiplicateur de gain selon le rang de la main"""
        payouts = {
            'royal_flush': 250,
            'straight_flush': 50,
            'four_of_a_kind': 25,
            'full_house': 9,
            'flush': 6,
            'straight': 4,
            'three_of_a_kind': 3,
            'two_pairs': 2,
            'pair': 1,
            'high_card': 0
        }
        return payouts.get(hand_rank, 0)

    def play_game(self, hold_indices=None):
        """Lance le jeu Video Poker"""
        # Distribution initiale
        deck = list(range(1, 53))
        random.shuffle(deck)
        
        self.initial_cards = [deck.pop() for _ in range(5)]
        
        # Échange des cartes (si hold_indices fourni)
        if hold_indices:
            held_cards = [self.initial_cards[i] for i in hold_indices]
            new_cards_needed = 5 - len(held_cards)
            new_cards = [deck.pop() for _ in range(new_cards_needed)]
            self.final_cards = held_cards + new_cards
        else:
            self.final_cards = self.initial_cards.copy()
        
        # Évaluer la main finale
        hand_rank = self.get_hand_rank(self.final_cards)
        self.hand_rank = hand_rank
        self.payout_multiplier = self.get_payout_multiplier(hand_rank)
        
        if self.payout_multiplier > 0:
            self.winnings = self.bet_amount * self.payout_multiplier
            self.result = 'win'
        else:
            self.result = 'lose'
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()