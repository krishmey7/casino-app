from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class OmahaPokerGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='omaha_poker_games')
    
    bet_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50.00'))
    hole_cards = models.JSONField(default=list)  # 4 cartes privées
    community_cards = models.JSONField(default=list)  # 5 cartes communes
    
    best_hand = models.JSONField(default=list)  # Meilleure main de 5 cartes
    hand_rank = models.CharField(max_length=20, null=True, blank=True)
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    result = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, default='finished')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Omaha Poker Game {self.id} - {self.player.username}"

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

    def get_best_hand(self):
        """Trouve la meilleure main de 5 cartes parmi les 9 cartes disponibles"""
        all_cards = self.hole_cards + self.community_cards
        best_rank = 'high_card'
        best_hand = []
        
        # Générer toutes les combinaisons de 5 cartes parmi 9
        from itertools import combinations
        for combo in combinations(all_cards, 5):
            combo_list = list(combo)
            rank = self.get_hand_rank(combo_list)
            if self._compare_hands(rank, best_rank, combo_list, best_hand):
                best_rank = rank
                best_hand = combo_list
        
        self.hand_rank = best_rank
        self.best_hand = best_hand
        return best_hand, best_rank

    def _compare_hands(self, rank1, rank2, hand1, hand2):
        """Compare deux mains pour déterminer laquelle est meilleure"""
        ranks_order = ['high_card', 'pair', 'two_pairs', 'three_of_a_kind', 'straight', 'flush', 'full_house', 'four_of_a_kind', 'straight_flush', 'royal_flush']
        
        rank1_index = ranks_order.index(rank1)
        rank2_index = ranks_order.index(rank2)
        
        if rank1_index > rank2_index:
            return True
        elif rank1_index < rank2_index:
            return False
        else:
            # Même rang, comparer les cartes individuelles
            return self._compare_same_rank(hand1, hand2, rank1)

    def _compare_same_rank(self, hand1, hand2, rank):
        """Compare deux mains du même rang"""
        ranks1 = sorted([card % 13 for card in hand1], reverse=True)
        ranks2 = sorted([card % 13 for card in hand2], reverse=True)
        
        for r1, r2 in zip(ranks1, ranks2):
            if r1 > r2:
                return True
            elif r1 < r2:
                return False
        return False

    def play_game(self):
        """Lance le jeu Omaha Poker"""
        # Distribution
        deck = list(range(1, 53))
        random.shuffle(deck)
        
        self.hole_cards = [deck.pop() for _ in range(4)]
        
        # Cartes communes (flop, turn, river)
        self.community_cards = [deck.pop() for _ in range(5)]
        
        # Trouver la meilleure main
        best_hand, hand_rank = self.get_best_hand()
        
        # Simulation d'un adversaire pour déterminer le résultat
        opponent_hole = [deck.pop() for _ in range(4)]
        opponent_best = self._get_opponent_best_hand(opponent_hole, self.community_cards)
        
        # Comparer les mains
        if self._compare_hands(hand_rank, opponent_best[1], best_hand, opponent_best[0]):
            self.winnings = self.bet_amount * Decimal('2')
            self.result = 'win'
        else:
            self.result = 'lose'
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()

    def _get_opponent_best_hand(self, hole_cards, community_cards):
        """Calcule la meilleure main de l'adversaire"""
        all_cards = hole_cards + community_cards
        best_rank = 'high_card'
        best_hand = []
        
        from itertools import combinations
        for combo in combinations(all_cards, 5):
            combo_list = list(combo)
            rank = self.get_hand_rank(combo_list)
            if self._compare_hands(rank, best_rank, combo_list, best_hand):
                best_rank = rank
                best_hand = combo_list
        
        return best_hand, best_rank