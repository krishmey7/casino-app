"""
Moteur de jeu LUDO
Coordonne la logique du jeu et applique les règles
"""

from typing import Dict, List, Optional, Tuple
from .rules import LudoRules


class LudoEngine:
    """Moteur principal du jeu LUDO"""
    
    def __init__(self, game_state: Dict = None):
        """
        Initialise le moteur avec un état de jeu existant ou un nouvel état
        """
        if game_state:
            self.game_state = game_state
        else:
            self.game_state = self.initialize_new_game()
    
    def initialize_new_game(self) -> Dict:
        """
        Initialise un nouvel état de jeu
        """
        return {
            "players": {},
            "dice": [],
            "last_dice_roll": None,
            "extra_turn": False,
            "captured_this_turn": False,
            "move_history": []
        }
    
    def add_player(self, color: str) -> None:
        """
        Ajoute un joueur à l'état du jeu
        """
        if "players" not in self.game_state:
            self.game_state["players"] = {}
        
        self.game_state["players"][color] = {
            "tokens": [-1, -1, -1, -1],  # 4 pions en base
            "finished_tokens": 0,
            "home_stretch": False
        }
    
    def roll_dice(self) -> List[int]:
        """
        Effectue un lancer de dés (côté serveur)
        """
        dice_result = LudoRules.roll_dice()
        self.game_state["dice"] = dice_result
        self.game_state["last_dice_roll"] = dice_result
        self.game_state["extra_turn"] = False
        self.game_state["captured_this_turn"] = False
        return dice_result
    
    def get_valid_moves_for_player(self, color: str) -> List[Dict]:
        """
        Retourne tous les mouvements valides pour un joueur
        """
        if not self.game_state["dice"]:
            return []
        
        dice_value = self.game_state["dice"][0]
        
        if color not in self.game_state["players"]:
            return []
        
        tokens = self.game_state["players"][color]["tokens"]
        
        # Récupérer tous les tokens de tous les joueurs
        all_players_tokens = {}
        for player_color, player_data in self.game_state["players"].items():
            all_players_tokens[player_color] = player_data["tokens"]
        
        valid_moves = LudoRules.get_valid_moves(
            tokens, dice_value, color, self.game_state, all_players_tokens
        )
        
        return valid_moves
    
    def execute_move(self, color: str, token_index: int) -> Dict:
        """
        Exécute un mouvement et retourne le résultat
        
        Args:
            color: Couleur du joueur
            token_index: Index du pion à déplacer
            
        Returns:
            Dict avec le résultat du mouvement
        """
        dice_value = self.game_state["dice"][0]
        tokens = self.game_state["players"][color]["tokens"]
        current_pos = tokens[token_index]
        
        # Récupérer tous les tokens de tous les joueurs
        all_players_tokens = {}
        for player_color, player_data in self.game_state["players"].items():
            all_players_tokens[player_color] = player_data["tokens"]
        
        # Valider le mouvement
        move = LudoRules.validate_token_move(
            token_index, current_pos, dice_value, color, all_players_tokens
        )
        
        if not move:
            return {"success": False, "error": "Mouvement invalide"}
        
        # Appliquer le mouvement
        new_pos = move["to"]
        tokens[token_index] = new_pos
        
        # Mettre à jour l'état du jeu
        if move["type"] == "enter_game":
            self.game_state["players"][color]["home_stretch"] = False
        elif new_pos >= 56:
            self.game_state["players"][color]["home_stretch"] = True
            
            # Vérifier si le pion est terminé
            if new_pos == 61:
                self.game_state["players"][color]["finished_tokens"] += 1
        
        # Gérer les captures
        captured = None
        if move.get("capture"):
            captured_color = move["capture"]
            captured = self.apply_capture(captured_color, new_pos)
            self.game_state["captured_this_turn"] = True
        
        # Vérifier tour supplémentaire
        extra_turn = LudoRules.gets_extra_turn(dice_value, captured is not None)
        self.game_state["extra_turn"] = extra_turn
        
        # Ajouter à l'historique
        self.game_state["move_history"].append({
            "color": color,
            "token_index": token_index,
            "from": current_pos,
            "to": new_pos,
            "dice": dice_value,
            "capture": captured
        })
        
        return {
            "success": True,
            "move": move,
            "extra_turn": extra_turn,
            "captured": captured
        }
    
    def apply_capture(self, captured_color: str, position: int) -> Optional[str]:
        """
        Applique une capture en retournant le pion capturé à sa base
        """
        if captured_color not in self.game_state["players"]:
            return None
        
        tokens = self.game_state["players"][captured_color]["tokens"]
        
        try:
            token_index = tokens.index(position)
            tokens[token_index] = -1  # Retour à la base
            return captured_color
        except ValueError:
            return None
    
    def check_victory(self, color: str) -> bool:
        """
        Vérifie si un joueur a gagné
        """
        if color not in self.game_state["players"]:
            return False
        
        tokens = self.game_state["players"][color]["tokens"]
        return LudoRules.check_victory(tokens)
    
    def get_all_players_tokens(self) -> Dict[str, List[int]]:
        """
        Retourne les positions de tous les pions de tous les joueurs
        """
        all_tokens = {}
        for color, player_data in self.game_state["players"].items():
            all_tokens[color] = player_data["tokens"]
        return all_tokens
    
    def get_player_state(self, color: str) -> Optional[Dict]:
        """
        Retourne l'état d'un joueur spécifique
        """
        return self.game_state["players"].get(color)
    
    def get_game_state(self) -> Dict:
        """
        Retourne l'état complet du jeu
        """
        return self.game_state.copy()
    
    def set_game_state(self, game_state: Dict) -> None:
        """
        Définit l'état du jeu
        """
        if LudoRules.validate_game_state(game_state):
            self.game_state = game_state
        else:
            raise ValueError("État de jeu invalide")
    
    def next_turn(self, current_turn: int, player_count: int) -> int:
        """
        Calcule le prochain tour
        """
        if self.game_state["extra_turn"]:
            return current_turn  # Le joueur garde son tour
        
        return LudoRules.get_next_turn(current_turn, player_count)
    
    def skip_turn(self) -> Dict:
        """
        Le joueur passe son tour (pas de mouvement possible)
        """
        self.game_state["extra_turn"] = False
        self.game_state["move_history"].append({
            "action": "skip_turn",
            "dice": self.game_state["dice"]
        })
        
        return {
            "success": True,
            "action": "skip_turn"
        }
    
    def get_move_history(self) -> List[Dict]:
        """
        Retourne l'historique des mouvements
        """
        return self.game_state.get("move_history", [])
    
    def reset_dice(self) -> None:
        """
        Réinitialise les dés pour le prochain tour
        """
        self.game_state["dice"] = []
        self.game_state["last_dice_roll"] = None
        self.game_state["extra_turn"] = False
        self.game_state["captured_this_turn"] = False
    
    def get_current_dice(self) -> Optional[List[int]]:
        """
        Retourne le résultat actuel des dés
        """
        return self.game_state.get("dice")
    
    def has_extra_turn(self) -> bool:
        """
        Vérifie si le joueur actuel a un tour supplémentaire
        """
        return self.game_state.get("extra_turn", False)
    
    def can_move(self, color: str) -> bool:
        """
        Vérifie si un joueur a des mouvements valides
        """
        valid_moves = self.get_valid_moves_for_player(color)
        return len(valid_moves) > 0
    
    def get_finished_tokens_count(self, color: str) -> int:
        """
        Retourne le nombre de pions terminés pour un joueur
        """
        if color not in self.game_state["players"]:
            return 0
        return self.game_state["players"][color]["finished_tokens"]
    
    def get_leaderboard(self) -> List[Tuple[str, int]]:
        """
        Retourne le classement basé sur le nombre de pions terminés
        """
        leaderboard = []
        for color, player_data in self.game_state["players"].items():
            finished = player_data["finished_tokens"]
            leaderboard.append((color, finished))
        
        # Trier par nombre de pions terminés (décroissant)
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        return leaderboard
