from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
import random

class ThreeCardPokerGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='three_card_poker_games')
    
    ante_bet = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50.00'))
    play_bet = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
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
        return f"Three Card Poker Game {self.id} - {self.player.username}"

    def get_hand_rank(self, cards):
        """Détermine le rang de la main"""
        ranks = [card % 13 for card in cards]
        ranks.sort(reverse=True)
        
        # Paire
        if ranks[0] == ranks[1] or ranks[1] == ranks[2]:
            return 'pair'
        
        # Flush (même couleur)
        suits = [card // 13 for card in cards]
        if len(set(suits)) == 1:
            return 'flush'
        
        # Straight (suite)
        if ranks[0] - ranks[1] == 1 and ranks[1] - ranks[2] == 1:
            return 'straight'
        
        # Straight flush
        if len(set(suits)) == 1 and ranks[0] - ranks[1] == 1 and ranks[1] - ranks[2] == 1:
            return 'straight_flush'
        
        # Three of a kind
        if ranks[0] == ranks[1] == ranks[2]:
            return 'three_of_a_kind'
        
        return 'high_card'

    def play_game(self):
        """Lance le jeu Three Card Poker"""
        # Tire 6 cartes
        deck = list(range(1, 53))
        all_cards = random.sample(deck, 6)
        self.player_cards = all_cards[:3]
        self.dealer_cards = all_cards[3:]
        
        self.player_hand_rank = self.get_hand_rank(self.player_cards)
        self.dealer_hand_rank = self.get_hand_rank(self.dealer_cards)
        
        # Le dealer doit avoir au moins une dame pour jouer
        dealer_qualifies = any(card % 13 >= 11 for card in self.dealer_cards)  # Dame = 11, Roi = 12, As = 0
        
        if not dealer_qualifies:
            # Dealer ne qualifie pas - joueur gagne ante
            self.winnings = self.ante_bet * Decimal('1')
            self.result = 'win'
        else:
            # Comparaison des mains
            rank_values = {
                'high_card': 0,
                'pair': 1,
                'flush': 2,
                'straight': 3,
                'three_of_a_kind': 4,
                'straight_flush': 5
            }
            
            player_value = rank_values[self.player_hand_rank]
            dealer_value = rank_values[self.dealer_hand_rank]
            
            if player_value > dealer_value:
                self.winnings = self.ante_bet * Decimal('1') + self.play_bet * Decimal('1')
                self.result = 'win'
            elif player_value < dealer_value:
                self.result = 'lose'
            else:
                # Même rang - comparaison haute carte
                player_high = max(card % 13 for card in self.player_cards)
                dealer_high = max(card % 13 for card in self.dealer_cards)
                if player_high > dealer_high:
                    self.winnings = self.ante_bet * Decimal('1') + self.play_bet * Decimal('1')
                    self.result = 'win'
                else:
                    self.result = 'lose'
        
        if self.result != 'win':
            self.winnings = Decimal('0')
        
        self.status = 'finished'
        self.ended_at = timezone.now()
        self.save()