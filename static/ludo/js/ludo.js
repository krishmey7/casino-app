/**
 * LUDO Frontend - Gestion WebSocket et Interface
 * 
 * Ce fichier gère :
 * - La connexion WebSocket avec reconnexion automatique
 * - La réception des états de jeu
 * - L'affichage des animations fluides
 * - Le déplacement visuel des pions
 * - L'affichage des états joueurs
 * - Les animations des dés
 * - Système de notifications modernes
 * 
 * IMPORTANT: Ce frontend NE calcule PAS les règles,
 * NE valide PAS les mouvements, NE génère PAS les dés.
 * Il envoie uniquement les actions et reçoit l'état.
 */

class LudoGame {
    constructor(gameId, playerColor, isCurrentTurn, gameState) {
        this.gameId = gameId;
        this.playerColor = playerColor;
        this.isCurrentTurn = isCurrentTurn;
        this.gameState = gameState;
        this.ws = null;
        this.validMoves = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 3000;
        this.notificationQueue = [];
        this.isProcessingNotification = false;
        
        this.init();
    }
    
    init() {
        this.initWebSocket();
        this.createTokens();
        this.renderBoard();
        this.setupEventListeners();
        this.updateTurnIndicator();
    }
    
    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/ludo/${this.gameId}/`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.reconnectAttempts = 0;
                this.reconnectDelay = 3000;
                this.showNotification('🟢 Connecté au jeu', 'success');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.showNotification('Erreur de connexion', 'error');
            };
            
            this.ws.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    this.showNotification(`Tentative de reconnexion (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`, 'warning');
                    setTimeout(() => this.initWebSocket(), this.reconnectDelay);
                    this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 30000);
                } else {
                    this.showNotification('❌ Connexion perdue. Veuillez rafraîchir la page.', 'error');
                }
            };
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            this.showNotification('Erreur de connexion au serveur', 'error');
        }
    }
    
    handleWebSocketMessage(data) {
        console.log('📨 WebSocket message:', data.type);
        
        switch(data.type) {
            case 'game_state':
                this.gameState = data.game.game_state;
                this.renderBoard();
                break;
            case 'dice_rolled':
                this.handleDiceRolled(data);
                break;
            case 'token_moved':
                this.handleTokenMoved(data);
                break;
            case 'turn_changed':
                this.handleTurnChanged(data);
                break;
            case 'turn_skipped':
                this.showNotification(`${data.player} a passé son tour`, 'info');
                break;
            case 'player_joined':
                this.showNotification(`👋 ${data.player} a rejoint la partie`, 'success');
                break;
            case 'player_disconnected':
                this.showNotification(`${data.player} s'est déconnecté`, 'warning');
                break;
            case 'player_ready':
                this.showNotification(`${data.player} est prêt`, 'success');
                break;
            case 'game_started':
                this.showNotification('🎮 La partie a commencé !', 'success');
                break;
            case 'game_cancelled':
                this.showNotification('❌ La partie a été annulée', 'error');
                setTimeout(() => window.location.href = '/ludo/lobby/', 2000);
                break;
            case 'victory':
                this.handleVictory(data);
                break;
            case 'error':
                this.showNotification(`⚠️ ${data.message}`, 'error');
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    handleDiceRolled(data) {
        const dice = document.getElementById('dice');
        const diceValue = document.getElementById('diceValue');
        
        if (dice && diceValue) {
            // Animation de rotation
            dice.classList.add('rolling');
            diceValue.style.display = 'none';
            dice.style.display = 'inline-flex';
            
            // Simuler plusieurs rotations
            let rotations = 0;
            const maxRotations = 10;
            const rotationInterval = setInterval(() => {
                rotations++;
                const randomValue = Math.floor(Math.random() * 6) + 1;
                dice.textContent = randomValue;
                
                if (rotations >= maxRotations) {
                    clearInterval(rotationInterval);
                    dice.classList.remove('rolling');
                    dice.style.display = 'none';
                    diceValue.style.display = 'inline-flex';
                    diceValue.textContent = data.dice[0];
                    this.showNotification(`🎲 Résultat: ${data.dice[0]}`, 'info');
                }
            }, 100);
        }
        
        this.fetchValidMoves();
    }
    
    handleTokenMoved(data) {
        this.gameState = data.game_state || this.gameState;
        this.renderBoard();
        
        if (data.captured) {
            this.showNotification(`💥 Pion capturé !`, 'warning');
        }
        
        if (data.extra_turn) {
            this.showNotification('🔄 Tour supplémentaire !', 'success');
        }
        
        if (data.victory) {
            this.showNotification(`🎉 ${data.winner} a gagné la partie !`, 'success');
        }
    }
    
    handleTurnChanged(data) {
        this.isCurrentTurn = data.current_color === this.playerColor;
        this.updateTurnIndicator();
        
        if (this.isCurrentTurn) {
            this.showNotification('🎯 C\'est votre tour !', 'success');
        } else {
            this.showNotification(`Tour de ${data.current_player}`, 'info');
        }
    }
    
    handleVictory(data) {
        this.showNotification(`🎉 ${data.winner} a gagné la partie !`, 'success');
        
        // Animation de victoire
        this.playVictoryAnimation();
        
        setTimeout(() => window.location.href = '/ludo/lobby/', 5000);
    }
    
    playVictoryAnimation() {
        // Confetti effect simple
        const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff'];
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.style.cssText = `
                position: fixed;
                width: 10px;
                height: 10px;
                background: ${colors[Math.floor(Math.random() * colors.length)]};
                left: ${Math.random() * 100}vw;
                top: -10px;
                border-radius: 50%;
                animation: fall ${2 + Math.random() * 2}s linear forwards;
                z-index: 10000;
            `;
            document.body.appendChild(confetti);
            
            setTimeout(() => confetti.remove(), 4000);
        }
        
        // Add keyframe animation if not exists
        if (!document.getElementById('victory-animation')) {
            const style = document.createElement('style');
            style.id = 'victory-animation';
            style.textContent = `
                @keyframes fall {
                    to {
                        transform: translateY(100vh) rotate(720deg);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    updateTurnIndicator() {
        const turnIndicator = document.getElementById('turnIndicator');
        const rollDiceBtn = document.getElementById('rollDiceBtn');
        const skipTurnBtn = document.getElementById('skipTurnBtn');
        
        if (turnIndicator) {
            if (this.isCurrentTurn) {
                turnIndicator.classList.add('active');
                turnIndicator.innerHTML = '🎯 C\'est votre tour !';
            } else {
                turnIndicator.classList.remove('active');
                turnIndicator.innerHTML = '⏳ Tour de l\'adversaire';
            }
        }
        
        if (rollDiceBtn) {
            rollDiceBtn.disabled = !this.isCurrentTurn;
        }
        
        if (skipTurnBtn) {
            skipTurnBtn.disabled = !this.isCurrentTurn;
        }
    }
    
    createTokens() {
        if (!this.gameState || !this.gameState.players) return;
        
        const board = document.getElementById('ludoBoard');
        if (!board) return;
        
        // Créer les tokens pour chaque joueur
        for (const [color, playerState] of Object.entries(this.gameState.players)) {
            const baseZone = document.querySelector(`.base-${color}`);
            if (!baseZone) continue;
            
            const slots = baseZone.querySelectorAll('.base-slot');
            if (slots.length < 4) continue;
            
            // Créer 4 tokens par joueur
            for (let i = 0; i < 4; i++) {
                const token = document.createElement('div');
                token.className = `token token-${color}`;
                token.dataset.color = color;
                token.dataset.index = i;
                token.addEventListener('click', () => this.handleTokenClick(color, i));
                slots[i].appendChild(token);
            }
        }
    }
    
    renderBoard() {
        if (!this.gameState || !this.gameState.players) return;
        
        // Parcourir tous les joueurs et mettre à jour les positions des pions
        for (const [color, playerState] of Object.entries(this.gameState.players)) {
            if (playerState.tokens) {
                playerState.tokens.forEach((position, index) => {
                    this.updateTokenPosition(color, index, position);
                });
            }
        }
        
        this.updateValidTokens();
    }
    
    updateTokenPosition(color, tokenIndex, position) {
        const token = document.querySelector(`.token[data-color="${color}"][data-index="${tokenIndex}"]`);
        if (!token) return;
        
        // Masquer si terminé
        if (position >= 56) {
            token.style.opacity = '0';
            token.style.transform = 'scale(0)';
            return;
        }
        
        token.style.opacity = '1';
        token.style.transform = 'scale(1)';
        
        // Si position = -1, mettre dans la base
        if (position === -1) {
            const baseZone = document.querySelector(`.base-${color}`);
            const slots = baseZone.querySelectorAll('.base-slot');
            if (slots[tokenIndex]) {
                slots[tokenIndex].appendChild(token);
            }
            return;
        }
        
        // Sinon, mettre dans la cellule du chemin correspondante
        const cellIndex = this.getCellIndex(position, color);
        if (cellIndex !== null) {
            const cells = document.querySelectorAll('.ludo-board > .cell');
            if (cells[cellIndex]) {
                cells[cellIndex].appendChild(token);
            }
        }
    }
    
    getCellIndex(position, color) {
        // Mapping des positions du jeu vers les indices des cellules dans la grille 15x15
        // La grille est organisée ligne par ligne (0-224 pour 15x15)
        
        // Ajuster la position selon la couleur de départ
        let adjustedPosition = position;
        if (color === 'blue') adjustedPosition = (position + 13) % 52;
        if (color === 'green') adjustedPosition = (position + 26) % 52;
        if (color === 'yellow') adjustedPosition = (position + 39) % 52;
        
        // Mapping du circuit principal (52 positions)
        const circuitMap = this.getCircuitMap();
        if (adjustedPosition < circuitMap.length) {
            return circuitMap[adjustedPosition];
        }
        
        return null;
    }
    
    getCircuitMap() {
        // Mapping des positions du circuit vers les indices des cellules dans la grille 15x15
        // Circuit standard LUDO: 52 positions en forme de croix
        // Grille organisée ligne par ligne (row * 15 + col)
        return [
            // Red path (haut horizontal) - ligne 1, colonnes 7-12 (indices 6-11)
            6, 7, 8, 9, 10, 11,
            // Red path vertical down - colonne 12, lignes 2-6 (indices 27, 42, 57, 72, 86)
            27, 42, 57, 72, 86,
            // Turn to blue path - colonne 12->7, ligne 6->7 (indices 86, 96)
            86, 96,
            // Blue path (horizontal gauche) - ligne 7, colonnes 1-6 (indices 90-95)
            90, 91, 92, 93, 94, 95,
            // Blue path vertical down - colonne 6, lignes 8-9 (indices 110, 125)
            110, 125,
            // Turn to green path - colonne 6->10, ligne 9->8 (indices 125, 114)
            125, 114,
            // Green path (horizontal droite) - ligne 8, colonnes 10-15 (indices 114-119)
            114, 115, 116, 117, 118, 119,
            // Green path vertical down - colonne 10, lignes 9-14 (indices 129, 144, 159, 174, 189, 204)
            129, 144, 159, 174, 189, 204,
            // Turn to yellow path - colonne 10->7, ligne 14->13 (indices 204, 193)
            204, 193,
            // Yellow path (horizontal gauche) - ligne 13, colonnes 7-9 (indices 193-195)
            193, 194, 195,
            // Yellow path vertical up - colonne 7, lignes 12-8 (indices 178, 163, 148, 133, 118)
            178, 163, 148, 133, 118,
            // Turn to red path - colonne 7->12, ligne 8->6 (indices 118, 86)
            118, 86
        ];
    }
    
    updateValidTokens() {
        // Mettre à jour les pions valides pour le mouvement
        document.querySelectorAll('.token').forEach(token => {
            const color = token.dataset.color;
            const index = parseInt(token.dataset.index);
            
            // Vérifier si ce pion est déplaçable
            const isValidMove = this.validMoves.some(move => 
                move.color === color && move.token_index === index
            );
            
            if (isValidMove && this.isCurrentTurn && color === this.playerColor) {
                token.classList.add('valid-move');
                token.style.cursor = 'pointer';
            } else {
                token.classList.remove('valid-move');
                token.style.cursor = 'default';
            }
        });
    }
    
    setupEventListeners() {
        const rollDiceBtn = document.getElementById('rollDiceBtn');
        const skipTurnBtn = document.getElementById('skipTurnBtn');
        const forfeitBtn = document.getElementById('forfeitBtn');
        
        if (rollDiceBtn) {
            rollDiceBtn.addEventListener('click', () => this.rollDice());
        }
        
        if (skipTurnBtn) {
            skipTurnBtn.addEventListener('click', () => this.skipTurn());
        }
        
        if (forfeitBtn) {
            forfeitBtn.addEventListener('click', () => this.forfeitGame());
        }
        
        // Ajouter les écouteurs d'événements pour les pions
        document.querySelectorAll('.token').forEach(token => {
            token.addEventListener('click', () => {
                const color = token.dataset.color;
                const index = parseInt(token.dataset.index);
                
                // Vérifier si le pion est valide
                const isValidMove = this.validMoves.some(move => 
                    move.color === color && move.token_index === index
                );
                
                if (isValidMove && this.isCurrentTurn && color === this.playerColor) {
                    this.moveToken(color, index);
                } else if (this.isCurrentTurn && color === this.playerColor) {
                    this.showNotification('Ce pion ne peut pas être déplacé', 'warning');
                }
            });
        });
    }
    
    rollDice() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.showNotification('⚠️ Connexion perdue. Tentative de reconnexion...', 'warning');
            return;
        }
        
        this.ws.send(JSON.stringify({ type: 'roll_dice' }));
    }
    
    moveToken(color, tokenIndex) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.showNotification('⚠️ Connexion perdue', 'warning');
            return;
        }
        
        this.ws.send(JSON.stringify({ 
            type: 'move_token',
            color: color,
            token_index: tokenIndex
        }));
    }
    
    skipTurn() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.showNotification('⚠️ Connexion perdue', 'warning');
            return;
        }
        
        this.ws.send(JSON.stringify({ type: 'skip_turn' }));
    }
    
    forfeitGame() {
        if (!confirm('⚠️ Êtes-vous sûr de vouloir abandonner ?')) {
            return;
        }
        
        fetch(`/ludo/forfeit/${this.gameId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Vous avez abandonné la partie', 'warning');
                setTimeout(() => window.location.href = '/ludo/lobby/', 2000);
            } else {
                this.showNotification(data.error || 'Erreur lors de l\'abandon', 'error');
            }
        })
        .catch(error => {
            console.error('Forfeit error:', error);
            this.showNotification('Erreur lors de l\'abandon', 'error');
        });
    }
    
    fetchValidMoves() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }
        
        this.ws.send(JSON.stringify({ type: 'get_valid_moves' }));
    }
    
    showNotification(message, type = 'info') {
        // Ajouter à la file d'attente
        this.notificationQueue.push({ message, type });
        
        // Traiter la file d'attente
        this.processNotificationQueue();
    }
    
    processNotificationQueue() {
        if (this.isProcessingNotification || this.notificationQueue.length === 0) {
            return;
        }
        
        this.isProcessingNotification = true;
        const { message, type } = this.notificationQueue.shift();
        
        this.displayNotification(message, type);
    }
    
    displayNotification(message, type) {
        // Créer le conteneur de notifications si n'existe pas
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(container);
        }
        
        // Créer la notification
        const notification = document.createElement('div');
        const colors = {
            success: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
            error: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
            warning: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            info: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
        };
        
        notification.style.cssText = `
            background: ${colors[type] || colors.info};
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            font-weight: 500;
            min-width: 300px;
            max-width: 400px;
            animation: slideIn 0.3s ease-out;
            cursor: pointer;
        `;
        notification.textContent = message;
        
        // Animation slide-in
        if (!document.getElementById('notification-animations')) {
            const style = document.createElement('style');
            style.id = 'notification-animations';
            style.textContent = `
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                @keyframes slideOut {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Click to dismiss
        notification.addEventListener('click', () => {
            this.dismissNotification(notification);
        });
        
        container.appendChild(notification);
        
        // Auto-dismiss
        setTimeout(() => {
            this.dismissNotification(notification);
        }, 4000);
    }
    
    dismissNotification(notification) {
        notification.style.animation = 'slideOut 0.3s ease-in forwards';
        setTimeout(() => {
            notification.remove();
            this.isProcessingNotification = false;
            this.processNotificationQueue();
        }, 300);
    }
    
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialisation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    // Les variables sont définies dans le template
    const gameId = window.gameId;
    const playerColor = window.playerColor;
    const isCurrentTurn = window.isCurrentTurn;
    const gameState = window.gameState;
    
    if (gameId && playerColor) {
        console.log('🎮 Initializing LUDO game...');
        window.ludoGame = new LudoGame(gameId, playerColor, isCurrentTurn, gameState);
    }
});
