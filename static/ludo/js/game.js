/**
 * Orchestrateur Principal du LUDO
 * Coordonne tous les modules et gère le flux du jeu
 */

class LudoGame {
  constructor(gameId, userId, options = {}) {
    this.gameId = gameId;
    this.userId = userId;
    this.options = {
      soundEnabled: true,
      animationsEnabled: true,
      autoReconnect: true,
      ...options
    };

    // Initialiser les modules
    this.board = null;
    this.animations = null;
    this.websocket = null;
    this.ui = null;

    // État du jeu
    this.gameState = {
      status: 'initializing',
      currentPlayer: null,
      currentDice: null,
      validMoves: [],
      players: [],
      moveHistory: []
    };

    // Événements
    this.eventCallbacks = {};
  }

  /**
   * Initialiser le jeu
   */
  async initialize() {
    try {
      console.log('Initialisation du jeu LUDO...');

      // Initialiser les modules
      await this.initializeModules();

      // Établir la connexion WebSocket
      this.connectWebSocket();

      // Configurer les écouteurs
      this.setupEventListeners();

      // Émettre l'événement d'initialisation
      this.emit('initialized');
      console.log('✓ Jeu LUDO initialisé avec succès');

    } catch (error) {
      console.error('Erreur lors de l\'initialisation du jeu:', error);
      this.ui.showError('Erreur lors du chargement du jeu');
      this.emit('initializationError', error);
    }
  }

  /**
   * Initialiser tous les modules
   */
  async initializeModules() {
    // Initialiser le plateau LUDO
    this.board = new LudoBoard();
    console.log('✓ Plateau LUDO initialisé');

    // Initialiser le système d'animations
    this.animations = new LudoAnimations(this.board);
    console.log('✓ Système d\'animations initialisé');

    // Initialiser l'interface utilisateur
    this.ui = new LudoUI();
    this.ui.setSoundEnabled(this.options.soundEnabled);
    console.log('✓ Interface utilisateur initialisée');

    // Attendre que le DOM soit complètement chargé
    if (document.readyState === 'loading') {
      await new Promise(resolve => {
        document.addEventListener('DOMContentLoaded', resolve);
      });
    }
  }

  /**
   * Établir la connexion WebSocket
   */
  connectWebSocket() {
    this.websocket = new LudoWebSocket(
      this.gameId,
      this.userId,
      (message) => this.handleWebSocketMessage(message)
    );

    // Événements WebSocket
    window.addEventListener('ludoWebSocketConnected', () => {
      this.onWebSocketConnected();
    });

    window.addEventListener('ludoWebSocketDisconnected', () => {
      this.onWebSocketDisconnected();
    });

    window.addEventListener('ludoReconnecting', (e) => {
      this.onWebSocketReconnecting(e.detail);
    });

    // Établir la connexion
    this.websocket.connect();
  }

  /**
   * Traiter un message WebSocket
   */
  handleWebSocketMessage(message) {
    console.log('Message reçu:', message.type);

    switch (message.type) {
      case 'game_state':
        this.updateGameState(message.data);
        break;

      case 'dice_rolled':
        this.handleDiceRolled(message.data);
        break;

      case 'piece_moved':
        this.handlePieceMoved(message.data);
        break;

      case 'piece_captured':
        this.handlePieceCaptured(message.data);
        break;

      case 'player_won':
        this.handlePlayerWon(message.data);
        break;

      case 'error':
        this.handleGameError(message.data);
        break;

      case 'chat_message':
        this.handleChatMessage(message.data);
        break;

      default:
        console.warn('Type de message inconnu:', message.type);
    }
  }

  /**
   * Mettre à jour l'état du jeu
   */
  updateGameState(newState) {
    this.gameState = { ...this.gameState, ...newState };
    console.log('État du jeu mis à jour:', this.gameState);

    // Mettre à jour l'interface utilisateur
    this.ui.displayGameState(this.gameState);

    this.emit('gameStateUpdated', this.gameState);
  }

  /**
   * Traiter le lancer de dés
   */
  async handleDiceRolled(data) {
    console.log('Dés lancés:', data.value);

    this.gameState.currentDice = data.value;

    // Animation des dés
    if (this.options.animationsEnabled) {
      const diceElements = document.querySelectorAll('.dice');
      await this.animations.animateDiceRoll(
        Array.from(diceElements),
        data.duration || 600
      );
    }

    // Mettre à jour l'affichage de la valeur des dés
    const diceDisplay = document.querySelector('.dice-value');
    if (diceDisplay) {
      diceDisplay.textContent = data.value;
    }

    // Jouer un son
    this.animations.playSound('dice');

    // Mettre à jour les coups valides
    if (data.valid_moves) {
      this.gameState.validMoves = data.valid_moves;
      this.ui.displayValidMoves(data.valid_moves);
    }

    this.emit('diceRolled', data);
  }

  /**
   * Traiter le déplacement d'un pion
   */
  async handlePieceMoved(data) {
    console.log('Pion déplacé:', data.piece_id);

    const piece = this.board.pieces.get(data.piece_id);
    if (!piece) {
      console.error('Pion non trouvé:', data.piece_id);
      return;
    }

    // Information de position
    const color = data.piece_id.split('-')[0]; // rouge, bleu, vert, jaune
    const newPosition = data.position;

    // Obtenir les coordonnées
    const newCoord = this.board.getCoordinates(color, newPosition);
    const currentCoord = {
      x: parseFloat(piece.style.left) || 0,
      y: parseFloat(piece.style.top) || 0
    };

    // Animer le mouvement
    if (this.options.animationsEnabled) {
      await this.animations.animateTokenMove(data.piece_id, currentCoord, newCoord);
      await this.animations.animateLanding(data.piece_id);
    }

    // Mettre à jour la position dans le DOM
    this.board.moveToken(data.piece_id, newPosition);

    // Jouer un son
    this.animations.playSound('move');

    // Ajouter à l'historique
    this.gameState.moveHistory.push({
      player: data.player_name,
      action: `A déplacé le pion de (${currentCoord.x}, ${currentCoord.y}) vers (${newCoord.x}, ${newCoord.y})`,
      timestamp: data.timestamp
    });

    this.emit('pieceMoved', data);
  }

  /**
   * Traiter la capture de pion
   */
  async handlePieceCaptured(data) {
    console.log('Pion capturé:', data.captured_piece_id);

    // Animation de capture
    if (this.options.animationsEnabled) {
      await this.animations.animateCapture(data.captured_piece_id);
    }

    // Jouer un son
    this.animations.playSound('capture');

    // Afficher une notification
    this.ui.showInfo(`Pion capturé par ${data.capturer_name}`);

    this.emit('pieceCaptured', data);
  }

  /**
   * Traiter la victoire d'un joueur
   */
  async handlePlayerWon(data) {
    console.log('Jeu terminé - Gagnant:', data.winner_name);

    // Animation de victoire
    if (this.options.animationsEnabled) {
      await this.animations.animateVictory();
    }

    // Jouer un son
    this.animations.playSound('victory');

    // Afficher l'écran de victoire
    this.ui.showVictoryScreen(data.winner_name, data.final_score);

    // Désactiver les contrôles
    this.ui.setGameControlsEnabled(false);

    this.emit('gameEnded', data);
  }

  /**
   * Traiter une erreur du jeu
   */
  handleGameError(data) {
    console.error('Erreur du jeu:', data.message);
    this.ui.showError(`Erreur: ${data.message}`);
    this.emit('gameError', data);
  }

  /**
   * Traiter un message de chat
   */
  handleChatMessage(data) {
    console.log('Message de chat reçu:', data.player_name);

    const chatPanel = document.querySelector('.chat-panel');
    if (chatPanel) {
      const messageElement = document.createElement('div');
      messageElement.className = 'chat-message';
      messageElement.innerHTML = `
        <span class="message-player">${data.player_name}:</span>
        <span class="message-content">${this.escapeHtml(data.message)}</span>
        <span class="message-time">${new Date(data.timestamp).toLocaleTimeString('fr-FR')}</span>
      `;
      chatPanel.appendChild(messageElement);
      chatPanel.scrollTop = chatPanel.scrollHeight;
    }
  }

  /**
   * Actions du joueur
   */

  /**
   * Lancer les dés
   */
  rollDice() {
    if (!this.websocket.isOpen()) {
      this.ui.showError('Connexion perdue. Reconnexion...');
      return;
    }

    console.log('Lancement des dés demandé');
    this.websocket.sendRollDice();
  }

  /**
   * Déplacer un pion
   */
  movepiece(pieceId, position) {
    if (!this.websocket.isOpen()) {
      this.ui.showError('Connexion perdue. Reconnexion...');
      return;
    }

    console.log('Déplacement du pion:', pieceId);
    this.websocket.sendMove(pieceId, position);
  }

  /**
   * Envoyer un message de chat
   */
  sendChatMessage(message) {
    if (!message.trim()) return;

    if (!this.websocket.isOpen()) {
      this.ui.showError('Connexion perdue. Impossible d\'envoyer le message.');
      return;
    }

    console.log('Envoi du message de chat');
    this.websocket.sendChatMessage(message);
  }

  /**
   * Gestion des connexions WebSocket
   */

  /**
   * Gestionnaire de connexion établie
   */
  onWebSocketConnected() {
    console.log('✓ Connecté au serveur');
    this.ui.showSuccess('Connecté au serveur');
    this.ui.updateConnectionStatus(true);
    this.emit('connected');
  }

  /**
   * Gestionnaire de connexion déconnectée
   */
  onWebSocketDisconnected() {
    console.log('✗ Déconnecté du serveur');
    this.ui.showWarning('Déconnecté du serveur');
    this.ui.updateConnectionStatus(false);
    this.emit('disconnected');
  }

  /**
   * Gestionnaire de reconnexion
   */
  onWebSocketReconnecting(detail) {
    console.log(`Tentative de reconnexion ${detail.attempt}/${5}...`);
    this.ui.showInfo(
      `Reconnexion en cours (tentative ${detail.attempt}/5)...`,
      0
    );
  }

  /**
   * Gestion des événements personnalisés
   */

  /**
   * S'abonner à un événement
   */
  on(eventName, callback) {
    if (!this.eventCallbacks[eventName]) {
      this.eventCallbacks[eventName] = [];
    }
    this.eventCallbacks[eventName].push(callback);
  }

  /**
   * Se désabonner d'un événement
   */
  off(eventName, callback) {
    if (this.eventCallbacks[eventName]) {
      this.eventCallbacks[eventName] = this.eventCallbacks[eventName].filter(
        cb => cb !== callback
      );
    }
  }

  /**
   * Émettre un événement
   */
  emit(eventName, data = null) {
    if (this.eventCallbacks[eventName]) {
      this.eventCallbacks[eventName].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Erreur dans le gestionnaire d'événement ${eventName}:`, error);
        }
      });
    }
  }

  /**
   * Utilitaires
   */

  /**
   * Échapper les caractères HTML
   */
  escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }

  /**
   * Configuration des écouteurs d'événements
   */
  setupEventListeners() {
    // Bouton de lancer de dés
    const rollDiceBtn = document.querySelector('[data-action="roll-dice"]');
    if (rollDiceBtn) {
      rollDiceBtn.addEventListener('click', () => this.rollDice());
    }

    // Sélection de coups valides
    document.addEventListener('moveSelected', (e) => {
      const move = this.gameState.validMoves.find(
        m => m.id === e.detail.moveId
      );
      if (move) {
        this.movepiece(move.piece_id, move.position);
      }
    });

    // Bouton de chat
    const chatForm = document.querySelector('.chat-form');
    if (chatForm) {
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = chatForm.querySelector('input[type="text"]');
        if (input.value) {
          this.sendChatMessage(input.value);
          input.value = '';
        }
      });
    }

    // Bouton de son
    const soundBtn = document.querySelector('.btn-toggle-sound');
    if (soundBtn) {
      soundBtn.addEventListener('click', () => {
        this.ui.toggleSound();
        this.animations.soundEnabled = this.ui.soundEnabled;
      });
    }
  }

  /**
   * Nettoyer et arrêter le jeu
   */
  destroy() {
    console.log('Arrêt du jeu LUDO');

    // Fermer la connexion WebSocket
    if (this.websocket) {
      this.websocket.close();
    }

    // Nettoyer les notifications
    if (this.ui) {
      this.ui.clearAllNotifications();
      this.ui.closeAllModals();
    }

    // Réinitialiser l'état
    this.eventCallbacks = {};
  }
}

// Exporter pour utilisation globale
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LudoGame;
}

// Initialiser le jeu au chargement de la page
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeGame);
} else {
  initializeGame();
}

/**
 * Fonction d'initialisation globale
 */
function initializeGame() {
  // Récupérer les paramètres
  const gameId = document.body.dataset.gameId;
  const userId = document.body.dataset.userId;

  if (!gameId || !userId) {
    console.error('Paramètres de jeu manquants');
    return;
  }

  // Créer et initialiser l'instance de jeu
  window.ludoGame = new LudoGame(gameId, userId, {
    soundEnabled: true,
    animationsEnabled: true,
    autoReconnect: true
  });

  window.ludoGame.initialize().catch(error => {
    console.error('Erreur lors de l\'initialisation:', error);
  });

  // Nettoyer à la fermeture de la page
  window.addEventListener('beforeunload', () => {
    if (window.ludoGame) {
      window.ludoGame.destroy();
    }
  });
}
