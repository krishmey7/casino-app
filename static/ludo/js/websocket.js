/**
 * Gestion WebSocket du LUDO
 * Gère la communication bidirectionnelle en temps réel avec le serveur Django Channels
 */

class LudoWebSocket {
  constructor(gameId, userId, onMessageCallback) {
    this.gameId = gameId;
    this.userId = userId;
    this.onMessage = onMessageCallback;
    
    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // ms
    this.messageQueue = [];
    this.pingInterval = null;
    this.protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  }

  /**
   * Établir la connexion WebSocket avec le serveur
   */
  connect() {
    try {
      const wsUrl = `${this.protocol}//${window.location.host}/ws/ludo/${this.gameId}/`;
      console.log('Connexion au WebSocket:', wsUrl);
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => this.onOpen();
      this.ws.onmessage = (event) => this.onMessageReceived(event);
      this.ws.onerror = (error) => this.onError(error);
      this.ws.onclose = () => this.onClose();
      
    } catch (error) {
      console.error('Erreur lors de la création du WebSocket:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Gestionnaire d'ouverture de connexion
   */
  onOpen() {
    console.log('✓ WebSocket connecté');
    this.isConnected = true;
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000; // Réinitialiser le délai
    
    // Envoyer les messages en attente
    this.flushMessageQueue();
    
    // Démarrer le ping périodique pour maintenir la connexion
    this.startPing();
    
    // Émettre un événement de connexion
    window.dispatchEvent(new CustomEvent('ludoWebSocketConnected'));
  }

  /**
   * Gestionnaire de fermeture de connexion
   */
  onClose() {
    console.log('✗ WebSocket fermé');
    this.isConnected = false;
    this.stopPing();
    
    // Émettre un événement de déconnexion
    window.dispatchEvent(new CustomEvent('ludoWebSocketDisconnected'));
    
    // Tenter une reconnexion
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    } else {
      console.error('Nombre maximal de tentatives de reconnexion atteint');
      window.dispatchEvent(new CustomEvent('ludoWebSocketFailed'));
    }
  }

  /**
   * Gestionnaire d'erreur de connexion
   */
  onError(error) {
    console.error('Erreur WebSocket:', error);
    window.dispatchEvent(new CustomEvent('ludoWebSocketError', {
      detail: { error: error.message }
    }));
  }

  /**
   * Traiter un message reçu du serveur
   */
  onMessageReceived(event) {
    try {
      const data = JSON.parse(event.data);
      console.log('Message reçu du serveur:', data.type, data);
      
      // Appeler le gestionnaire de message fourni
      if (this.onMessage) {
        this.onMessage(data);
      }
      
      // Émettre un événement personnalisé
      window.dispatchEvent(new CustomEvent('ludoMessage', {
        detail: data
      }));
      
    } catch (error) {
      console.error('Erreur lors du traitement du message:', error, event.data);
    }
  }

  /**
   * Envoyer un message au serveur
   */
  send(messageType, data = {}) {
    const message = {
      type: messageType,
      ...data
    };
    
    if (this.isConnected) {
      try {
        this.ws.send(JSON.stringify(message));
        console.log('Message envoyé:', message.type);
      } catch (error) {
        console.error('Erreur lors de l\'envoi du message:', error);
        this.messageQueue.push(message);
      }
    } else {
      console.warn('WebSocket non connecté, mise en file d\'attente du message:', message.type);
      this.messageQueue.push(message);
    }
  }

  /**
   * Envoyer un coup de jeu
   */
  sendMove(pieceId, position) {
    this.send('move', {
      piece_id: pieceId,
      position: position,
      timestamp: Date.now()
    });
  }

  /**
   * Envoyer un lancer de dés
   */
  sendRollDice() {
    this.send('roll_dice', {
      timestamp: Date.now()
    });
  }

  /**
   * Envoyer un message de chat
   */
  sendChatMessage(message) {
    this.send('chat_message', {
      content: message,
      timestamp: Date.now()
    });
  }

  /**
   * Envoyer un message de statut de joueur
   */
  sendPlayerStatus(status) {
    this.send('player_status', {
      status: status, // 'ready', 'playing', 'waiting', 'left'
      timestamp: Date.now()
    });
  }

  /**
   * File d'attente des messages
   */
  flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      try {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify(message));
        } else {
          this.messageQueue.unshift(message); // Remettre en queue
          break;
        }
      } catch (error) {
        console.error('Erreur lors de l\'envoi du message en queue:', error);
        this.messageQueue.unshift(message); // Remettre en queue
        break;
      }
    }
  }

  /**
   * Programmer une reconnexion avec backoff exponentiel
   */
  scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`Reconnexion dans ${delay}ms (tentative ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    window.dispatchEvent(new CustomEvent('ludoReconnecting', {
      detail: { attempt: this.reconnectAttempts, delay: delay }
    }));
    
    setTimeout(() => this.connect(), delay);
  }

  /**
   * Démarrer le ping périodique pour maintenir la connexion
   */
  startPing() {
    // Envoyer un ping toutes les 30 secondes
    this.pingInterval = setInterval(() => {
      if (this.isConnected) {
        this.send('ping', {
          timestamp: Date.now()
        });
      }
    }, 30000);
  }

  /**
   * Arrêter le ping périodique
   */
  stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Vérifier l'état de la connexion
   */
  isOpen() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Fermer la connexion proprement
   */
  close() {
    this.stopPing();
    if (this.ws) {
      try {
        this.ws.close(1000, 'Fermeture normale');
      } catch (error) {
        console.error('Erreur lors de la fermeture du WebSocket:', error);
      }
    }
    this.isConnected = false;
  }

  /**
   * Réinitialiser l'état de la connexion
   */
  reset() {
    this.close();
    this.messageQueue = [];
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000;
  }

  /**
   * Types de messages supportés (pour référence)
   */
  static MessageTypes = {
    // Messages de jeu
    MOVE: 'move',
    ROLL_DICE: 'roll_dice',
    CHAT_MESSAGE: 'chat_message',
    PLAYER_STATUS: 'player_status',
    
    // Messages du serveur
    GAME_STATE: 'game_state',
    PIECE_MOVED: 'piece_moved',
    DICE_ROLLED: 'dice_rolled',
    PIECE_CAPTURED: 'piece_captured',
    PLAYER_WON: 'player_won',
    GAME_ENDED: 'game_ended',
    
    // Messages de système
    PING: 'ping',
    PONG: 'pong',
    ERROR: 'error'
  };
}

// Exporter pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LudoWebSocket;
}
