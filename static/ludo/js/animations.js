/**
 * Animations LUDO
 * Gère les animations fluides et accélérées par GPU pour les événements du jeu
 */

class LudoAnimations {
  constructor(board) {
    this.board = board;
    this.soundEnabled = true;
    this.animationQueue = [];
    this.isAnimating = false;
  }

  /**
   * Animer le déplacement d'un pion d'une position à l'autre
   * Utilise l'animation keyframe pour un mouvement fluide
   */
  async animateTokenMove(pieceId, fromCoord, toCoord, duration = 400) {
    const token = this.board.pieces.get(pieceId);
    if (!token) return;

    return new Promise(resolve => {
      // Créer l'animation
      const startTime = performance.now();
      
      const animate = (currentTime) => {
        const progress = Math.min((currentTime - startTime) / duration, 1);
        
        // Fonction d'assouplissement: cubic-bezier(0.4, 0, 0.2, 1)
        const easeProgress = this.cubicBezier(progress, 0.4, 0, 0.2, 1);
        
        // Interpoler la position
        const currentX = fromCoord.x + (toCoord.x - fromCoord.x) * easeProgress;
        const currentY = fromCoord.y + (toCoord.y - fromCoord.y) * easeProgress;
        
        // Appliquer la transformation
        token.style.transform = `translate3d(${currentX}px, ${currentY}px, 0)`;
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          resolve();
        }
      };
      
      requestAnimationFrame(animate);
    });
  }

  /**
   * Animer le lancer de dés avec effet de rotation 3D
   */
  async animateDiceRoll(diceElements, duration = 600) {
    const startTime = performance.now();
    
    return new Promise(resolve => {
      diceElements.forEach(dice => {
        dice.classList.add('rolling');
        
        const animate = (currentTime) => {
          const progress = Math.min((currentTime - startTime) / duration, 1);
          const rotation = progress * 1440; // 4 rotations complètes
          
          dice.style.transform = `rotateX(${rotation}deg) rotateY(${rotation * 0.5}deg) rotateZ(${rotation * 1.2}deg)`;
          
          if (progress < 1) {
            requestAnimationFrame(animate);
          } else {
            dice.classList.remove('rolling');
            dice.style.transform = 'rotateX(0) rotateY(0) rotateZ(0)';
            resolve();
          }
        };
        
        requestAnimationFrame(animate);
      });
    });
  }

  /**
   * Animer la capture de pion - réduction d'échelle et fondu
   */
  async animateCapture(capturedPieceId, duration = 300) {
    const token = this.board.pieces.get(capturedPieceId);
    if (!token) return;

    return new Promise(resolve => {
      const startTime = performance.now();
      
      const animate = (currentTime) => {
        const progress = Math.min((currentTime - startTime) / duration, 1);
        const easeProgress = this.cubicBezier(progress, 0.4, 0, 0.2, 1);
        
        const scale = 1 - easeProgress * 0.8;
        const opacity = 1 - easeProgress;
        
        token.style.transform += ` scale(${scale})`;
        token.style.opacity = opacity;
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          this.board.removeToken(capturedPieceId);
          resolve();
        }
      };
      
      requestAnimationFrame(animate);
    });
  }

  /**
   * Animation de pulsation pour la mise en évidence des mouvements valides
   */
  animatePulse(pieceId, duration = 1500, scale = 1.15) {
    const token = this.board.pieces.get(pieceId);
    if (!token) return;

    const startTime = performance.now();
    
    const animate = (currentTime) => {
      const progress = ((currentTime - startTime) % duration) / duration;
      
      // Assouplissement de pulsation
      const pulseProgress = Math.sin(progress * Math.PI * 2) * 0.5 + 0.5;
      const currentScale = 1 + (scale - 1) * pulseProgress;
      
      if (token.dataset.animating !== 'false') {
        token.style.filter = `drop-shadow(0 0 ${12 + pulseProgress * 8}px currentColor)`;
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }

  /**
   * Animer la victoire - effet de particules/confettis
   */
  async animateVictory(duration = 1500) {
    const container = document.querySelector('.board-wrapper');
    if (!container) return;

    const particleCount = 30;
    
    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement('div');
      particle.style.position = 'absolute';
      particle.style.width = '8px';
      particle.style.height = '8px';
      particle.style.background = this.getRandomColor();
      particle.style.borderRadius = '50%';
      particle.style.pointerEvents = 'none';
      particle.style.zIndex = '100';
      
      const startX = Math.random() * 100;
      const startY = 50;
      const angle = (Math.random() - 0.5) * Math.PI;
      const velocity = 2 + Math.random() * 3;
      
      particle.style.left = startX + '%';
      particle.style.top = startY + '%';
      
      container.appendChild(particle);
      
      const startTime = performance.now();
      
      const animate = (currentTime) => {
        const progress = Math.min((currentTime - startTime) / duration, 1);
        const easeProgress = progress; // Linéaire pour les particules
        
        const x = startX + Math.cos(angle) * velocity * progress * 100;
        const y = startY + Math.sin(angle) * velocity * progress * 100 + (progress * progress * 50);
        const opacity = 1 - progress;
        
        particle.style.left = x + '%';
        particle.style.top = y + '%';
        particle.style.opacity = opacity;
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          particle.remove();
        }
      };
      
      requestAnimationFrame(animate);
    }

    return new Promise(resolve => setTimeout(resolve, duration));
  }

  /**
   * Animation de rebond pour les pions à l'atterrissage
   */
  async animateLanding(pieceId, duration = 400) {
    const token = this.board.pieces.get(pieceId);
    if (!token) return;

    const bounces = 3;
    const bounceHeight = 8; // pixels
    
    return new Promise(resolve => {
      const startTime = performance.now();
      const currentCoord = {
        x: parseFloat(token.style.transform.match(/translateX\(([-\d.]+)px/)?.[1] || 0),
        y: parseFloat(token.style.transform.match(/translateY\(([-\d.]+)px/)?.[1] || 0)
      };
      
      const animate = (currentTime) => {
        const progress = Math.min((currentTime - startTime) / duration, 1);
        
        // Courbe de rebond (onde sinusoïdale avec amplitude décroissante)
        const bouncePhase = progress * bounces * Math.PI * 2;
        const bounceAmplitude = (1 - progress) * bounceHeight;
        const bounce = Math.sin(bouncePhase) * bounceAmplitude;
        
        token.style.transform = `translate3d(${currentCoord.x}px, ${currentCoord.y - bounce}px, 0)`;
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          token.style.transform = `translate3d(${currentCoord.x}px, ${currentCoord.y}px, 0)`;
          resolve();
        }
      };
      
      requestAnimationFrame(animate);
    });
  }

  /**
   * Animation de secousse pour les états d'erreur
   */
  async animateShake(targetElement, duration = 400) {
    return new Promise(resolve => {
      const startTime = performance.now();
      const shakeDistance = 5; // pixels
      
      const animate = (currentTime) => {
        const progress = Math.min((currentTime - startTime) / duration, 1);
        const shakePhase = progress * duration / 125; // Ajustement de fréquence
        
        const shakeX = Math.sin(shakePhase * Math.PI * 2) * shakeDistance * (1 - progress);
        
        targetElement.style.transform = `translateX(${shakeX}px)`;
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          targetElement.style.transform = 'translateX(0)';
          resolve();
        }
      };
      
      requestAnimationFrame(animate);
    });
  }

  /**
   * Animation d'éclair pour les événements importants
   */
  async animateFlash(targetElement, duration = 600, color = 'rgba(255, 215, 0, 0.8)') {
    return new Promise(resolve => {
      const startTime = performance.now();
      const originalShadow = targetElement.style.boxShadow;
      
      const animate = (currentTime) => {
        const progress = Math.min((currentTime - startTime) / duration, 1);
        const easeProgress = Math.sin(progress * Math.PI) * 2; // Courbe en cloche
        
        const shadowSize = 20 * easeProgress;
        targetElement.style.boxShadow = `0 0 ${shadowSize}px ${color}`;
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          targetElement.style.boxShadow = originalShadow;
          resolve();
        }
      };
      
      requestAnimationFrame(animate);
    });
  }

  /**
   * Fonction d'assouplissement Cubic Bezier
   */
  cubicBezier(t, p0, p1, p2, p3) {
    const mt = 1 - t;
    return (mt * mt * mt * p0) +
           (3 * mt * mt * t * p1) +
           (3 * mt * t * t * p2) +
           (t * t * t * p3);
  }

  /**
   * Obtenir une couleur aléatoire pour les particules
   */
  getRandomColor() {
    const colors = [
      '#ef4444', // rouge
      '#3b82f6', // bleu
      '#22c55e', // vert
      '#eab308', // jaune
      '#fbbf24', // or
      '#ec4899'  // rose
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  }

  /**
   * Jouer un effet sonore (si activé)
   */
  playSound(soundType = 'move') {
    if (!this.soundEnabled) return;

    // URLs de son pour les différents événements
    const sounds = {
      'dice': '/static/ludo/sounds/dice.mp3',
      'move': '/static/ludo/sounds/move.mp3',
      'capture': '/static/ludo/sounds/capture.mp3',
      'victory': '/static/ludo/sounds/victory.mp3'
    };

    const soundUrl = sounds[soundType];
    if (soundUrl) {
      try {
        const audio = new Audio(soundUrl);
        audio.volume = 0.3; // Volume réduit
        audio.play().catch(e => console.debug('Lecture audio empêchée:', e));
      } catch (e) {
        console.debug('Lecture sonore non disponible:', e);
      }
    }
  }

  /**
   * Activer/désactiver le son
   */
  setSoundEnabled(enabled) {
    this.soundEnabled = enabled;
  }

  /**
   * File d'attente d'animation pour exécution séquentielle
   */
  queueAnimation(animationFn) {
    this.animationQueue.push(animationFn);
    this.processQueue();
  }

  /**
   * Traiter la file d'attente d'animation
   */
  async processQueue() {
    if (this.isAnimating || this.animationQueue.length === 0) return;
    
    this.isAnimating = true;
    const animation = this.animationQueue.shift();
    
    try {
      await animation();
    } catch (e) {
      console.error('Erreur d\'animation:', e);
    }
    
    this.isAnimating = false;
    this.processQueue();
  }
}

// Exporter pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LudoAnimations;
}
