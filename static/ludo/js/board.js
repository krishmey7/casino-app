/**
 * Gestionnaire du Plateau LUDO
 * Gère le système de coordonnées du plateau, le placement des pions et l'état du plateau
 */

class LudoBoard {
  constructor() {
    // Dimensions du plateau
    this.boardSize = 560; // Taille de la boîte de visualisation SVG
    this.tokenLayer = document.getElementById('tokens-layer');
    this.pieces = new Map(); // Map<pieceId, Element>
    
    // Initialiser le système de coordonnées
    this.initializeCoordinateSystem();
  }

  /**
   * Initialiser le système de coordonnées du plateau
   * Mappe les positions logiques aux coordonnées SVG
   */
  initializeCoordinateSystem() {
    // Coordonnées de base comme référence
    const cellSize = 40; // Coordonnées SVG approximatives par cellule
    
    // Définir toutes les positions du plateau
    // Format position: {x: pourcentage de la largeur, y: pourcentage de la hauteur}
    // Cela permet la mise à l'échelle responsive
    
    this.positions = {
      // POSITIONS ROUGE (chemin latéral gauche allant vers le haut)
      red: {
        base: [
          { x: 8, y: 8, id: 'red-base-0' },    // Slot base rouge 0
          { x: 25, y: 8, id: 'red-base-1' },   // Slot base rouge 1
          { x: 8, y: 25, id: 'red-base-2' },   // Slot base rouge 2
          { x: 25, y: 25, id: 'red-base-3' }   // Slot base rouge 3
        ],
        path: [
          { x: 25, y: 50, id: 'red-start' },   // Position de départ (0)
          { x: 25, y: 41, id: 'red-1' },       // (1)
          { x: 25, y: 32, id: 'red-2' },       // (2)
          { x: 25, y: 23, id: 'red-3' },       // (3)
          { x: 25, y: 14, id: 'red-safe' },    // Zone sûre
          { x: 50, y: 5, id: 'red-home' }      // Maison
        ],
        // Chemin principal pour le rouge
        mainPath: [
          { x: 25, y: 50 },  // 0: Départ
          { x: 25, y: 41 },  // 1
          { x: 25, y: 32 },  // 2
          { x: 25, y: 23 },  // 3
          { x: 50, y: 9 },   // 4 (zone sûre en haut)
          { x: 59, y: 25 },  // 5: Traverser vers bleu
          { x: 68, y: 25 },  // 6
          { x: 77, y: 25 },  // 7
          { x: 86, y: 25 },  // 8
          { x: 86, y: 50 },  // 9: Zone sûre bleu
          { x: 75, y: 75 },  // 10: Traverser vers vert
          { x: 75, y: 84 },  // 11
          { x: 75, y: 93 },  // 12
          { x: 50, y: 91 }   // 13: Zone sûre vert
        ]
      },
      
      // POSITIONS BLEU (chemin supérieur allant vers la droite)
      blue: {
        base: [
          { x: 75, y: 8, id: 'blue-base-0' },   // Slot base bleu 0
          { x: 92, y: 8, id: 'blue-base-1' },   // Slot base bleu 1
          { x: 75, y: 25, id: 'blue-base-2' },  // Slot base bleu 2
          { x: 92, y: 25, id: 'blue-base-3' }   // Slot base bleu 3
        ],
        path: [
          { x: 50, y: 25, id: 'blue-start' },   // Position de départ (0)
          { x: 59, y: 25, id: 'blue-1' },       // (1)
          { x: 68, y: 25, id: 'blue-2' },       // (2)
          { x: 77, y: 25, id: 'blue-3' },       // (3)
          { x: 86, y: 25, id: 'blue-safe' },    // Zone sûre
          { x: 93, y: 50, id: 'blue-home' }     // Maison
        ],
        mainPath: [
          { x: 50, y: 25 },  // 0: Départ
          { x: 59, y: 25 },  // 1
          { x: 68, y: 25 },  // 2
          { x: 77, y: 25 },  // 3
          { x: 86, y: 25 },  // 4 (safe)
          { x: 75, y: 50 },  // 5: Traverser vers le bas
          { x: 75, y: 75 },  // 6
          { x: 50, y: 86 },  // 7: Zone sûre verte
          { x: 25, y: 75 },  // 8: Traverser vers jaune
          { x: 14, y: 75 },  // 9
          { x: 9, y: 50 }    // 10: Zone sûre jaune
        ]
      },

      // POSITIONS VERT (chemin latéral droit allant vers le bas)
      green: {
        base: [
          { x: 8, y: 75, id: 'green-base-0' },   // Slot base vert 0
          { x: 25, y: 75, id: 'green-base-1' },  // Slot base vert 1
          { x: 8, y: 92, id: 'green-base-2' },   // Slot base vert 2
          { x: 25, y: 92, id: 'green-base-3' }   // Slot base vert 3
        ],
        path: [
          { x: 75, y: 50, id: 'green-start' },   // Position de départ (0)
          { x: 75, y: 59, id: 'green-1' },       // (1)
          { x: 75, y: 68, id: 'green-2' },       // (2)
          { x: 75, y: 77, id: 'green-3' },       // (3)
          { x: 75, y: 86, id: 'green-safe' },    // Zone sûre
          { x: 50, y: 93, id: 'green-home' }     // Maison
        ],
        mainPath: [
          { x: 75, y: 50 },  // 0: Départ
          { x: 75, y: 59 },  // 1
          { x: 75, y: 68 },  // 2
          { x: 77, y: 77 },  // 3
          { x: 75, y: 86 },  // 4 (safe)
          { x: 50, y: 75 },  // 5: Traverser à gauche
          { x: 25, y: 75 },  // 6
          { x: 14, y: 50 },  // 7: Zone sûre jaune
          { x: 25, y: 25 },  // 8: Traverser vers le haut
          { x: 50, y: 14 }   // 9: Zone sûre rouge
        ]
      },

      // POSITIONS JAUNE (chemin inférieur allant vers la gauche)
      yellow: {
        base: [
          { x: 75, y: 75, id: 'yellow-base-0' },  // Slot base jaune 0
          { x: 92, y: 75, id: 'yellow-base-1' },  // Slot base jaune 1
          { x: 75, y: 92, id: 'yellow-base-2' },  // Slot base jaune 2
          { x: 92, y: 92, id: 'yellow-base-3' }   // Slot base jaune 3
        ],
        path: [
          { x: 50, y: 75, id: 'yellow-start' },   // Position de départ (0)
          { x: 41, y: 75, id: 'yellow-1' },       // (1)
          { x: 32, y: 75, id: 'yellow-2' },       // (2)
          { x: 23, y: 75, id: 'yellow-3' },       // (3)
          { x: 14, y: 75, id: 'yellow-safe' },    // Zone sûre
          { x: 7, y: 50, id: 'yellow-home' }      // Maison
        ],
        mainPath: [
          { x: 50, y: 75 },  // 0: Départ
          { x: 41, y: 75 },  // 1
          { x: 32, y: 75 },  // 2
          { x: 23, y: 75 },  // 3
          { x: 14, y: 75 },  // 4 (safe)
          { x: 25, y: 50 },  // 5: Traverser vers le haut
          { x: 25, y: 25 },  // 6
          { x: 50, y: 14 }   // 7: Zone sûre rouge
        ]
      }
    };
  }

  /**
   * Obtenir les coordonnées SVG pour un pion à une position donnée
   * @param {string} color - Couleur du joueur (rouge, bleu, vert, jaune)
   * @param {number} position - Index de position (-1 = base, 0-51 = chemin, 52+ = maison)
   * @param {number} baseIndex - Quel slot de base (0-3) si en base
   * @returns {object} {x, y, id} en coordonnées SVG
   */
  getCoordinates(color, position, baseIndex = 0) {
    if (!this.positions[color]) {
      console.warn(`Couleur invalide: ${color}`);
      return { x: 0, y: 0, id: '' };
    }

    // Si en base (-1)
    if (position === -1) {
      const basePos = this.positions[color].base[baseIndex % 4];
      return this.convertPercentageToCoordinates(basePos);
    }

    // Si allant à la maison (position >= 56)
    if (position >= 56) {
      const homePos = this.positions[color].path[5]; // position maison
      return this.convertPercentageToCoordinates(homePos);
    }

    // Positions du chemin principal
    if (position >= 0 && position < 6) {
      const pathPos = this.positions[color].path[position];
      return this.convertPercentageToCoordinates(pathPos);
    }

    // Si au-delà de la dernière longueur, afficher à la maison
    return this.convertPercentageToCoordinates(this.positions[color].path[5]);
  }

  /**
   * Convertir les coordonnées en pourcentage en coordonnées SVG réelles
   * @param {object} percentPos - {x: pourcentage, y: pourcentage}
   * @returns {object} {x, y} en unités SVG
   */
  convertPercentageToCoordinates(percentPos) {
    return {
      x: (percentPos.x / 100) * this.boardSize,
      y: (percentPos.y / 100) * this.boardSize,
      id: percentPos.id
    };
  }

  /**
   * Rendre un pion sur le plateau
   * @param {string} pieceId - Identifiant unique du pion
   * @param {string} color - Couleur du joueur
   * @param {number} position - Position actuelle sur le plateau
   * @param {number} baseIndex - Index du slot de base si en base
   */
  renderToken(pieceId, color, position, baseIndex = 0) {
    const coords = this.getCoordinates(color, position, baseIndex);
    
    // Créer ou mettre à jour l'élément du pion
    let token = this.pieces.get(pieceId);
    if (!token) {
      token = document.createElement('div');
      token.id = pieceId;
      token.className = `token ${color}`;
      this.tokenLayer.appendChild(token);
      this.pieces.set(pieceId, token);
    }

    // Positionner le pion aux coordonnées calculées
    // Décalage de la moitié de la taille du pion pour le centrer
    const tokenSize = 32; // 2rem en pixels (32px)
    const offsetX = coords.x - tokenSize / 2;
    const offsetY = coords.y - tokenSize / 2;

    // Utiliser la transformation accélérée par GPU
    token.style.transform = `translate3d(${offsetX}px, ${offsetY}px, 0)`;
  }

  /**
   * Déplacer un pion vers une nouvelle position avec animation
   * @param {string} pieceId - Pion à déplacer
   * @param {string} color - Couleur du joueur
   * @param {number} newPosition - Nouvelle position
   * @param {number} baseIndex - Slot de base si applicable
   * @param {number} duration - Durée de l'animation en ms
   */
  async moveToken(pieceId, color, newPosition, baseIndex = 0, duration = 300) {
    // Signal pour le système d'animation
    const token = this.pieces.get(pieceId);
    if (token) {
      token.dataset.animating = 'true';
    }

    // Rendre la nouvelle position
    this.renderToken(pieceId, color, newPosition, baseIndex);

    // Attendre la fin de l'animation
    await new Promise(resolve => setTimeout(resolve, duration));

    if (token) {
      token.dataset.animating = 'false';
    }
  }

  /**
   * Supprimer un pion du plateau
   * @param {string} pieceId - Pion à supprimer
   */
  removeToken(pieceId) {
    const token = this.pieces.get(pieceId);
    if (token) {
      token.remove();
      this.pieces.delete(pieceId);
    }
  }

  /**
   * Effacer tous les pions du plateau
   */
  clearAllTokens() {
    this.pieces.forEach(token => token.remove());
    this.pieces.clear();
  }

  /**
   * Obtenir tous les pions d'une couleur spécifique
   * @param {string} color - Couleur du joueur
   * @returns {array} Tableau d'IDs de pions
   */
  getTokensByColor(color) {
    const tokens = [];
    this.pieces.forEach((element, pieceId) => {
      if (element.classList.contains(color)) {
        tokens.push(pieceId);
      }
    });
    return tokens;
  }

  /**
   * Mettre à jour les indicateurs de mouvements valides pour les pions
   * @param {array} validMoveIds - Tableau d'IDs de pions ayant des mouvements valides
   */
  setValidMoves(validMoveIds = []) {
    // Effacer les mouvements valides précédents
    this.pieces.forEach(token => {
      token.classList.remove('valid-move');
    });

    // Marquer les nouveaux mouvements valides
    validMoveIds.forEach(pieceId => {
      const token = this.pieces.get(pieceId);
      if (token) {
        token.classList.add('valid-move');
      }
    });
  }

  /**
   * Obtenir les dimensions du plateau utiles pour la mise à l'échelle responsive
   */
  getBoardDimensions() {
    const wrapper = document.querySelector('.board-wrapper');
    if (wrapper) {
      return {
        width: wrapper.offsetWidth,
        height: wrapper.offsetHeight
      };
    }
    return { width: this.boardSize, height: this.boardSize };
  }

  /**
   * Initialiser l'état du plateau à partir des données du serveur
   * @param {object} gameState - État du jeu du serveur
   */
  renderGameState(gameState) {
    this.clearAllTokens();

    // Rendre tous les pions à partir de l'état du jeu
    if (gameState.players) {
      Object.entries(gameState.players).forEach(([color, playerData]) => {
        playerData.tokens.forEach((position, tokenIndex) => {
          const pieceId = `${color}-token-${tokenIndex}`;
          const baseIndex = tokenIndex;
          this.renderToken(pieceId, color, position, baseIndex);
        });
      });
    }
  }
}

// Exporter pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LudoBoard;
}
