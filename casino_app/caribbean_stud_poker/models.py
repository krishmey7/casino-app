from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class CaribbeanStudPokerGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='caribbean_stud_poker_games')
    
    ante_bet = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50.00'))
    call_bet = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    player_cards = models.JSONField(default=list)
    dealer_cards = models.JSONField(default=list)
    
    player_hand_rank = models.CharField(max_length=20, null=True, blank=True)
    dealer_hand_rank = models.CharField(max_length=20, null=True, blank=True)
    
    winnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), null=True, blank=True)
    result = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, default='finished')
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Caribbean Stud Poker Game {self.id} - {self.player.username}"

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
        """Lance le jeu Caribbean Stud Poker"""
        # Tire 10 cartes
        deck = list(range(1, 53))
        all_cards = random.sample(deck, 10)
        self.player_cards = all_cards[:5]
        self.dealer_cards = all_cards[5:]
        
        self.player_hand_rank = self.get_hand_rank(self.player_cards)
        self.dealer_hand_rank = self.get_hand_rank(self.dealer_cards)
        
        # Le dealer doit avoir au moins As-Roi pour jouer
        dealer_qualifies = self.get_hand_rank(self.dealer_cards) in ['one_pair', 'two_pair', 'three_of_a_kind', 'straight', 'flush', 'full_house', 'four_of_a_kind', 'straight_flush', 'royal_flush']
        
        if not dealer_qualifies:
            # Dealer ne qualifie pas - joueur gagne ante
            self.winnings = self.ante_bet * Decimal('1')
            self.result = 'win'
        else:
            # Comparaison des mains
            rank_values = {
                'high_card': 0,
                'one_pair': 1,
                'two_pair': 2,
                'three_of_a_kind': 3,
                'straight': 4,
                'flush': 5,
                'full_house': 6,
                'four_of_a_kind': 7,
                'straight_flush': 8,
                'royal_flush': 9
            }
            
            player_value = rank_values[self.player_hand_rank]
            dealer_value = rank_values[self.dealer_hand_rank]
            
            if player_value > dealer_value:
                # Joueur gagne - paiements selon la main
                payouts = {
                    'one_pair': 1,
                    'two_pair': 2,
                    'three_of_a_kind': 3,
                    'straight': 4,
                    'flush': 5,
                    'full_house': 7,
                    'four_of_a_kind': 20,
                    'straight_flush': 50,
                    'royal_flush': 100
                }
                multiplier = payouts.get(self.player_hand_rank, 1)
                self.winnings = self.ante_bet * multiplier + self.call_bet * Decimal('2')
                self.result = 'win'
            elif player_value < dealer_value:
                self.result = 'lose'
            else:
                # Même rang - comparaison détaillée (simplifiée)
                self.result = 'lose'  # Pour simplifier
        
        if self.result != 'win':
            self.winnings = Decimal('0')
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()