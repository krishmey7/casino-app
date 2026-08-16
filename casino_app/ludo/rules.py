"""
Règles du jeu LUDO
Toute la logique de validation des règles est ici
"""

import random
from typing import Dict, List, Tuple, Optional


class LudoRules:
    """Classe contenant toutes les règles du jeu LUDO"""
    
    # Configuration du plateau
    BOARD_SIZE = 52  # Cases principales (13 par couleur)
    HOME_STRETCH_SIZE = 5  # Cases dans la zone d'arrivée
    TOTAL_TOKENS_PER_PLAYER = 4
    
    # Positions de départ pour chaque couleur
    START_POSITIONS = {
        'red': 0,
        'blue': 13,
        'green': 26,
        'yellow': 39
    }
    
    # Positions d'entrée dans la zone d'arrivée
    HOME_ENTRY_POSITIONS = {
        'red': 50,
        'blue': 11,
        'green': 24,
        'yellow': 37
    }
    
    # Positions des bases (où les pions commencent)
    BASE_POSITIONS = {
        'red': [-1, -1, -1, -1],
        'blue': [-1, -1, -1, -1],
        'green': [-1, -1, -1, -1],
        'yellow': [-1, -1, -1, -1]
    }
    
    @staticmethod
    def roll_dice() -> List[int]:
        """
        Génère le résultat des dés (côté serveur uniquement)
        Retourne une liste de 1 ou 2 dés selon les règles
        """
        # Pour LUDO standard, on utilise un seul dé
        return [random.randint(1, 6)]
    
    @staticmethod
    def can_enter_game(dice_value: int) -> bool:
        """
        Vérifie si un pion peut entrer en jeu avec le résultat du dé
        Un 6 est nécessaire pour sortir un pion de la base
        """
        return dice_value == 6
    
    @staticmethod
    def get_valid_moves(
        tokens: List[int],
        dice_value: int,
        color: str,
        game_state: Dict,
        all_players_tokens: Dict[str, List[int]]
    ) -> List[Dict]:
        """
        Retourne les mouvements valides pour les pions d'un joueur
        
        Args:
            tokens: Positions des 4 pions du joueur
            dice_value: Valeur du dé
            color: Couleur du joueur
            game_state: État global du jeu
            all_players_tokens: Positions de tous les pions de tous les joueurs
            
        Returns:
            Liste des mouvements valides sous forme de dictionnaires
        """
        valid_moves = []
        
        for token_index, token_pos in enumerate(tokens):
            move = LudoRules.validate_token_move(
                token_index, token_pos, dice_value, color, all_players_tokens
            )
            if move:
                valid_moves.append(move)
        
        return valid_moves
    
    @staticmethod
    def validate_token_move(
        token_index: int,
        token_pos: int,
        dice_value: int,
        color: str,
        all_players_tokens: Dict[str, List[int]]
    ) -> Optional[Dict]:
        """
        Valide un mouvement spécifique pour un pion
        
        Returns:
            Dict avec le mouvement valide ou None si invalide
        """
        # Pion dans la base
        if token_pos == -1:
            if not LudoRules.can_enter_game(dice_value):
                return None
            
            # Vérifier si la position de départ est libre
            start_pos = LudoRules.START_POSITIONS[color]
            if LudoRules.is_position_occupied(start_pos, color, all_players_tokens):
                return None
            
            return {
                'token_index': token_index,
                'from': token_pos,
                'to': start_pos,
                'type': 'enter_game'
            }
        
        # Pion sur le plateau
        new_pos = LudoRules.calculate_new_position(token_pos, dice_value, color)
        
        # Vérifier si le mouvement est valide (pas au-delà de la fin)
        if new_pos is None:
            return None
        
        # Vérifier si la nouvelle position est libre ou capturable
        if LudoRules.is_position_occupied(new_pos, color, all_players_tokens):
            # La position est occupée par un pion de la même couleur
            return None
        
        # Vérifier si c'est une capture
        captured = LudoRules.check_capture(new_pos, color, all_players_tokens)
        
        return {
            'token_index': token_index,
            'from': token_pos,
            'to': new_pos,
            'type': 'move',
            'capture': captured
        }
    
    @staticmethod
    def calculate_new_position(current_pos: int, dice_value: int, color: str) -> Optional[int]:
        """
        Calcule la nouvelle position d'un pion après un mouvement
        
        Returns:
            Nouvelle position ou None si le mouvement est invalide (dépasser la fin)
        """
        # Vérifier si le pion est dans la zone d'arrivée
        if current_pos >= 56:  # Dans la zone d'arrivée
            home_stretch_pos = current_pos - 56
            new_home_stretch_pos = home_stretch_pos + dice_value
            
            if new_home_stretch_pos > 5:  # Dépasse la fin
                return None
            
            return 56 + new_home_stretch_pos
        
        # Vérifier si le pion doit entrer dans la zone d'arrivée
        home_entry = LudoRules.HOME_ENTRY_POSITIONS[color]
        if current_pos <= home_entry <= current_pos + dice_value:
            # Le pion va entrer dans la zone d'arrivée
            steps_to_entry = home_entry - current_pos
            remaining_steps = dice_value - steps_to_entry
            return 56 + remaining_steps
        
        # Mouvement normal sur le plateau
        new_pos = (current_pos + dice_value) % 52
        return new_pos
    
    @staticmethod
    def is_position_occupied(position: int, current_color: str, all_players_tokens: Dict[str, List[int]]) -> bool:
        """
        Vérifie si une position est occupée par un pion de la même couleur
        """
        for color, tokens in all_players_tokens.items():
            if color == current_color:
                # Vérifier si un de nos pions est à cette position
                if position in tokens and position != -1:
                    return True
        return False
    
    @staticmethod
    def check_capture(position: int, current_color: str, all_players_tokens: Dict[str, List[int]]) -> Optional[str]:
        """
        Vérifie si un pion peut être capturé à cette position
        
        Returns:
            Couleur du joueur capturé ou None si pas de capture
        """
        for color, tokens in all_players_tokens.items():
            if color != current_color:
                if position in tokens and position != -1 and position < 56:
                    return color
        return None
    
    @staticmethod
    def check_victory(tokens: List[int]) -> bool:
        """
        Vérifie si un joueur a gagné (tous ses pions terminés)
        """
        # Tous les pions doivent être à la position 61 (fin)
        return all(token == 61 for token in tokens)
    
    @staticmethod
    def gets_extra_turn(dice_value: int, captured: bool = False) -> bool:
        """
        Détermine si le joueur obtient un tour supplémentaire
        - Toujours vrai si le dé montre 6
        - Vrai si capture (selon certaines variantes)
        """
        return dice_value == 6 or captured
    
    @staticmethod
    def get_next_turn(current_turn: int, player_count: int) -> int:
        """
        Calcule le prochain joueur
        """
        return (current_turn + 1) % player_count
    
    @staticmethod
    def apply_capture(
        captured_color: str,
        all_players_tokens: Dict[str, List[int]],
        position: int
    ) -> Dict:
        """
        Applique une capture: le pion capturé retourne à sa base
        
        Returns:
            Mise à jour des tokens du joueur capturé
        """
        if captured_color not in all_players_tokens:
            return {}
        
        tokens = all_players_tokens[captured_color]
        
        # Trouver l'index du pion capturé
        try:
            token_index = tokens.index(position)
            # Retourner à la base
            tokens[token_index] = -1
            return {captured_color: tokens}
        except ValueError:
            return {}
    
    @staticmethod
    def get_safe_positions() -> List[int]:
        """
        Retourne les positions sûres (où les captures ne sont pas possibles)
        Dans LUDO standard: positions 0, 8, 13, 21, 26, 34, 39, 47
        """
        return [0, 8, 13, 21, 26, 34, 39, 47]
    
    @staticmethod
    def is_safe_position(position: int) -> bool:
        """
        Vérifie si une position est sûre
        """
        return position in LudoRules.get_safe_positions()
    
    @staticmethod
    def validate_game_state(game_state: Dict) -> bool:
        """
        Valide l'intégrité de l'état du jeu
        """
        required_keys = ['players', 'dice', 'last_dice_roll', 'extra_turn', 'captured_this_turn']
        
        if not all(key in game_state for key in required_keys):
            return False
        
        # Valider la structure des joueurs
        if 'players' not in game_state:
            return False
        
        for color, player_data in game_state['players'].items():
            if 'tokens' not in player_data:
                return False
            if 'finished_tokens' not in player_data:
                return False
            if 'home_stretch' not in player_data:
                return False
            
            # Valider les tokens
            tokens = player_data['tokens']
            if len(tokens) != 4:
                return False
            
            # Valider les positions des tokens
            for token in tokens:
                if token == -1:  # Base
                    continue
                if token < 0 or token > 61:  # Position invalide
                    return False
        
        return True
