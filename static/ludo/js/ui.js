/**
 * Composants UI du LUDO
 * Gère les notifications, les modales, les contrôles et l'interface utilisateur
 */

class LudoUI {
  constructor() {
    this.notifications = [];
    this.modals = {};
    this.soundEnabled = true;
    this.initializeElements();
  }

  /**
   * Initialiser les éléments DOM principaux
   */
  initializeElements() {
    // Créer les conteneurs si ils n'existent pas
    if (!document.querySelector('.notification-container')) {
      const notificationContainer = document.createElement('div');
      notificationContainer.className = 'notification-container';
      document.body.appendChild(notificationContainer);
    }

    if (!document.querySelector('.modales-container')) {
      const modalesContainer = document.createElement('div');
      modalesContainer.className = 'modales-container';
      document.body.appendChild(modalesContainer);
    }

    // Initialiser les réactions aux événements
    this.setupEventListeners();
  }

  /**
   * Configurer les écouteurs d'événements
   */
  setupEventListeners() {
    // Gestion du clic en dehors des modales
    document.addEventListener('click', (e) => {
      const modal = e.target.closest('.modal');
      if (!modal && !e.target.closest('[role="button"]')) {
        this.closeAllModals();
      }
    });
  }

  /**
   * Afficher une notification
   */
  showNotification(message, type = 'info', duration = 4000) {
    const container = document.querySelector('.notification-container');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.setAttribute('role', 'alert');
    
    const content = document.createElement('div');
    content.className = 'notification-content';
    content.textContent = message;
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'notification-close';
    closeBtn.setAttribute('aria-label', 'Fermer la notification');
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', () => this.removeNotification(notification));
    
    notification.appendChild(content);
    notification.appendChild(closeBtn);
    container.appendChild(notification);
    
    this.notifications.push(notification);
    
    // Animation d'apparition
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Fermeture automatique
    if (duration > 0) {
      setTimeout(() => this.removeNotification(notification), duration);
    }

    return notification;
  }

  /**
   * Retirer une notification
   */
  removeNotification(notification) {
    notification.classList.remove('show');
    setTimeout(() => {
      notification.remove();
      this.notifications = this.notifications.filter(n => n !== notification);
    }, 300);
  }

  /**
   * Afficher une notification de succès
   */
  showSuccess(message, duration = 3000) {
    return this.showNotification(message, 'success', duration);
  }

  /**
   * Afficher une notification d'erreur
   */
  showError(message, duration = 5000) {
    return this.showNotification(message, 'error', duration);
  }

  /**
   * Afficher une notification d'avertissement
   */
  showWarning(message, duration = 4000) {
    return this.showNotification(message, 'warning', duration);
  }

  /**
   * Afficher une notification d'information
   */
  showInfo(message, duration = 3000) {
    return this.showNotification(message, 'info', duration);
  }

  /**
   * Créer et afficher une modale
   */
  createModal(title, content, buttons = []) {
    const container = document.querySelector('.modales-container');
    if (!container) return null;

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    if (title) modal.setAttribute('aria-label', title);

    const header = document.createElement('div');
    header.className = 'modal-header';
    
    const titleElement = document.createElement('h2');
    titleElement.className = 'modal-title';
    titleElement.textContent = title;
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'modal-close';
    closeBtn.setAttribute('aria-label', 'Fermer la boîte de dialogue');
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', () => this.closeModal(modal));
    
    header.appendChild(titleElement);
    header.appendChild(closeBtn);

    const body = document.createElement('div');
    body.className = 'modal-body';
    
    if (typeof content === 'string') {
      body.innerHTML = content;
    } else if (content instanceof HTMLElement) {
      body.appendChild(content);
    }

    const footer = document.createElement('div');
    footer.className = 'modal-footer';
    
    buttons.forEach(buttonConfig => {
      const btn = document.createElement('button');
      btn.className = `btn btn-${buttonConfig.type || 'primary'}`;
      btn.textContent = buttonConfig.text;
      btn.addEventListener('click', () => {
        if (buttonConfig.callback) buttonConfig.callback();
        if (buttonConfig.autoClose !== false) {
          this.closeModal(modal);
        }
      });
      footer.appendChild(btn);
    });

    modal.appendChild(header);
    modal.appendChild(body);
    modal.appendChild(footer);
    
    container.appendChild(modal);
    
    // Animation d'apparition
    setTimeout(() => modal.classList.add('show'), 10);
    
    // Stocker la référence
    const modalId = `modal-${Date.now()}`;
    this.modals[modalId] = modal;
    
    return modal;
  }

  /**
   * Fermer une modale spécifique
   */
  closeModal(modal) {
    if (modal) {
      modal.classList.remove('show');
      setTimeout(() => {
        modal.remove();
        for (let key in this.modals) {
          if (this.modals[key] === modal) {
            delete this.modals[key];
            break;
          }
        }
      }, 300);
    }
  }

  /**
   * Fermer toutes les modales
   */
  closeAllModals() {
    Object.values(this.modals).forEach(modal => this.closeModal(modal));
  }

  /**
   * Afficher une modale de confirmation
   */
  showConfirmDialog(title, message, onConfirm, onCancel) {
    const modal = this.createModal(title, `<p>${message}</p>`, [
      {
        text: 'Annuler',
        type: 'secondary',
        callback: onCancel || (() => {}),
        autoClose: true
      },
      {
        text: 'Confirmer',
        type: 'primary',
        callback: onConfirm || (() => {}),
        autoClose: true
      }
    ]);
    return modal;
  }

  /**
   * Afficher une modale d'alerte
   */
  showAlertDialog(title, message, onClose) {
    const modal = this.createModal(title, `<p>${message}</p>`, [
      {
        text: 'OK',
        type: 'primary',
        callback: onClose || (() => {}),
        autoClose: true
      }
    ]);
    return modal;
  }

  /**
   * Mettre à jour la fiche joueur
   */
  updatePlayerCard(playerData) {
    const cardContainer = document.querySelector(`.player-card[data-player-id="${playerData.id}"]`);
    if (!cardContainer) return;

    // Mettre à jour les informations
    const nameElement = cardContainer.querySelector('.player-name');
    if (nameElement) nameElement.textContent = playerData.name;

    const scoreElement = cardContainer.querySelector('.player-score');
    if (scoreElement) scoreElement.textContent = `Score: ${playerData.score || 0}`;

    const statusElement = cardContainer.querySelector('.player-status');
    if (statusElement) statusElement.textContent = playerData.status || 'en attente';

    const statusBadge = cardContainer.querySelector('.status-badge');
    if (statusBadge) {
      statusBadge.className = `status-badge status-${playerData.status}`;
    }
  }

  /**
   * Afficher la liste des coups valides
   */
  displayValidMoves(moves) {
    const validMovesPanel = document.querySelector('.valid-moves-panel');
    if (!validMovesPanel) return;

    validMovesPanel.innerHTML = '';
    
    if (moves.length === 0) {
      validMovesPanel.innerHTML = '<p class="no-moves">Aucun coup valide</p>';
      return;
    }

    const title = document.createElement('h3');
    title.textContent = 'Coups valides';
    validMovesPanel.appendChild(title);

    const list = document.createElement('ul');
    list.className = 'moves-list';
    
    moves.forEach((move, index) => {
      const item = document.createElement('li');
      item.className = 'move-item';
      item.innerHTML = `
        <span class="move-number">${index + 1}</span>
        <span class="move-description">${move.description}</span>
        <button class="btn-select-move" data-move-id="${move.id}">
          Sélectionner
        </button>
      `;
      
      item.querySelector('.btn-select-move').addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('moveSelected', {
          detail: { moveId: move.id }
        }));
      });
      
      list.appendChild(item);
    });

    validMovesPanel.appendChild(list);
  }

  /**
   * Afficher l'historique des coups
   */
  displayMoveHistory(moves) {
    const historyPanel = document.querySelector('.move-history-panel');
    if (!historyPanel) return;

    historyPanel.innerHTML = '';
    
    const title = document.createElement('h3');
    title.textContent = 'Historique des coups';
    historyPanel.appendChild(title);

    const list = document.createElement('ul');
    list.className = 'history-list';
    
    moves.slice(-10).reverse().forEach(move => {
      const item = document.createElement('li');
      item.className = 'history-item';
      item.innerHTML = `
        <span class="history-player">${move.player}</span>
        <span class="history-action">${move.action}</span>
        <span class="history-time">${this.formatTime(move.timestamp)}</span>
      `;
      list.appendChild(item);
    });

    historyPanel.appendChild(list);
  }

  /**
   * Formater un timestamp en temps lisible
   */
  formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Il y a moins d\'une minute';
    if (diff < 3600000) return `Il y a ${Math.floor(diff / 60000)} minutes`;
    if (diff < 86400000) return `Il y a ${Math.floor(diff / 3600000)} heures`;
    
    return date.toLocaleDateString('fr-FR');
  }

  /**
   * Afficher l'état du jeu en temps réel
   */
  displayGameState(gameState) {
    // Mettre à jour le tour actuel
    const currentTurnElement = document.querySelector('.current-turn');
    if (currentTurnElement) {
      currentTurnElement.textContent = `Joueur actuel: ${gameState.currentPlayer}`;
    }

    // Mettre à jour le dé
    const diceElement = document.querySelector('.dice-value');
    if (diceElement && gameState.lastDice) {
      diceElement.textContent = gameState.lastDice;
    }

    // Mettre à jour les fiches joueurs
    gameState.players.forEach(player => {
      this.updatePlayerCard(player);
    });
  }

  /**
   * Afficher une animation de victoire
   */
  showVictoryScreen(winnerName, finalScore) {
    const modal = this.createModal('Victoire!', `
      <div class="victory-content">
        <h1>${winnerName} a gagné!</h1>
        <p class="victory-score">Score final: ${finalScore}</p>
        <p class="victory-message">Félicitations!</p>
      </div>
    `, [
      {
        text: 'Nouvelle partie',
        type: 'primary',
        callback: () => window.dispatchEvent(new CustomEvent('startNewGame')),
        autoClose: true
      },
      {
        text: 'Accueil',
        type: 'secondary',
        callback: () => window.location.href = '/',
        autoClose: true
      }
    ]);
    return modal;
  }

  /**
   * Activer/désactiver les contrôles du jeu
   */
  setGameControlsEnabled(enabled) {
    const buttons = document.querySelectorAll('[data-game-action="true"]');
    buttons.forEach(btn => {
      btn.disabled = !enabled;
      btn.classList.toggle('disabled', !enabled);
    });
  }

  /**
   * Afficher un indicateur de chargement
   */
  showLoadingIndicator(message = 'Chargement...') {
    const loader = document.createElement('div');
    loader.className = 'loading-indicator';
    loader.innerHTML = `
      <div class="spinner"></div>
      <p>${message}</p>
    `;
    document.body.appendChild(loader);
    return loader;
  }

  /**
   * Masquer l'indicateur de chargement
   */
  hideLoadingIndicator() {
    const loader = document.querySelector('.loading-indicator');
    if (loader) {
      loader.style.opacity = '0';
      setTimeout(() => loader.remove(), 300);
    }
  }

  /**
   * Gérer l'affichage du son
   */
  toggleSound() {
    this.soundEnabled = !this.soundEnabled;
    const btn = document.querySelector('.btn-toggle-sound');
    if (btn) {
      btn.classList.toggle('sound-off', !this.soundEnabled);
      btn.setAttribute('aria-label', this.soundEnabled ? 'Désactiver le son' : 'Activer le son');
    }
    return this.soundEnabled;
  }

  /**
   * Afficher l'état de la connexion
   */
  updateConnectionStatus(connected) {
    const indicator = document.querySelector('.connection-indicator');
    if (indicator) {
      indicator.classList.toggle('connected', connected);
      indicator.classList.toggle('disconnected', !connected);
      indicator.textContent = connected ? '● Connecté' : '● Déconnecté';
    }
  }

  /**
   * Nettoyer toutes les notificiations
   */
  clearAllNotifications() {
    this.notifications.forEach(notification => {
      notification.remove();
    });
    this.notifications = [];
  }
}

// Exporter pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LudoUI;
}
