# Analyse Complète - Jeu Face ou Pile BO3

## 📋 Table des matières
1. [Vue d'ensemble](#vue-densemble)
2. [Architecture Backend](#architecture-backend)
3. [Architecture Frontend](#architecture-frontend)
4. [Flux de jeu](#flux-de-jeu)
5. [WebSocket & Synchronisation](#websocket--synchronisation)
6. [Animations & UI](#animations--ui)
7. [Points d'amélioration potentiels](#points-damélioration-potentiels)

---

## Vue d'ensemble

Le jeu **Face ou Pile BO3** est une implémentation multijoueur en temps réel d'un jeu de pile ou face au meilleur des 3 manches. Les joueurs misent une somme, et le premier à remporter 2 manches gagne 95% du pot total.

### Caractéristiques principales
- **Format BO3** (Best of 3) : Premier à 2 victoires
- **Mise en jeu** : Chaque joueur mise le même montant
- **Distribution des gains** : 95% du pot au gagnant (5% commission)
- **Choix alterné** : J1 choisit en manche 1, J2 en manche 2, tirage au sort en manche 3
- **Synchronisation temps réel** : WebSocket pour synchroniser l'animation de la pièce
- **Animations 3D** : Pièce avec rendu CSS 3D et animations synchronisées

---

## Architecture Backend

### 1. Modèle de données (`models.py`)

#### Classe `FaceOuPileGame`

**Champs principaux :**
```python
player1 = ForeignKey(User, related_name='fop_games_as_player1')
player2 = ForeignKey(User, related_name='fop_games_as_player2', null=True)
bet_amount = DecimalField(max_digits=10, decimal_places=2)
player1_choice = CharField(max_length=10, choices=CHOICES, null=True)
coin_result = CharField(max_length=10, choices=CHOICES, null=True)
winner = ForeignKey(User, related_name='fop_wins', null=True)
status = CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
```

**Champs BO3 :**
```python
player1_score = IntegerField(default=0)  # Score J1 (max 2)
player2_score = IntegerField(default=0)  # Score J2 (max 2)
current_round = IntegerField(default=1)  # Manche actuelle (1-3)
round_chooser = CharField(max_length=10, null=True)  # 'player1' ou 'player2'
round_results = JSONField(default=list)  # Historique des manches
```

**Méthodes clés :**

- `setup_round()` : Configure la manche actuelle
  - Manche 1 : player1 choisit
  - Manche 2 : player2 choisit
  - Manche 3 : tirage aléatoire
  - Reset du choix et résultat

- `flip_coin()` : Effectue le tirage aléatoire 50/50
  - Retourne 'face' ou 'pile' aléatoirement

- `determine_round_winner()` : Détermine le gagnant de la manche
  - Compare le choix du chooser avec le résultat
  - Retourne le joueur gagnant

- `complete_round()` : Termine la manche et met à jour les scores
  - Incrémente le score du gagnant
  - Enregistre le résultat dans `round_results`
  - Vérifie si la partie est terminée (score >= 2)
  - Si terminé : définit le winner et le status
  - Sinon : passe à la manche suivante

- `determine_game_winner()` : Détermine le gagnant du BO3
  - Premier joueur à atteindre 2 points

- `payout()` : Distribution des gains
  - Calcule le pot total (mise × 2)
  - Crédite 95% du pot au gagnant via Wallet
  - 5% de commission pour la maison

**Note importante sur le stockage des choix :**
- Seul le choix du `round_chooser` actuel est stocké dans `player1_choice`
- Le choix de l'adversaire est déduit dynamiquement (opposé du chooser)
- Pas de champ `player2_choice` distinct

---

### 2. Serializer (`serializers.py`)

#### Classe `FaceOuPileGameSerializer`

**Champs exposés :**
```python
fields = [
    'id', 'player1', 'player2', 'bet_amount',
    'player1_choice', 'player2_choice', 'coin_result',
    'winner', 'status', 'created_at', 'finished_at',
    'result', 'player1_score', 'player2_score',
    'current_round', 'round_chooser', 'round_results',
    'opponent_choice',
]
```

**Méthodes calculées :**

- `get_player2_choice()` : Retourne l'opposé du choix de player1 (legacy)
- `get_opponent_choice()` : Retourne le choix de l'adversaire pour la manche actuelle
  - Utilise `player1_choice` comme source du chooser
  - Déduit l'opposé via `get_opponent_choice()`
- `get_result()` : Retourne le gagnant de la manche actuelle

**Champs read-only :**
- winner, status, finished_at, result, coin_result, player2_choice
- player1_score, player2_score, current_round, round_chooser, round_results, opponent_choice

---

### 3. API Views (`api_views.py`)

#### Classe `FaceOuPileGameViewSet`

**Endpoints disponibles :**

1. **`POST /api/face_ou_pile/games/create_game/`**
   - Crée une nouvelle partie
   - Déduit la mise du wallet du créateur
   - Configure la manche 1 (player1 choisit)
   - Retourne le jeu créé

2. **`POST /api/face_ou_pile/games/{id}/join_game/`**
   - Permet à un joueur de rejoindre une partie en attente
   - Déduit la mise du wallet du joueur 2
   - Passe le statut à 'playing'
   - Retourne le jeu mis à jour

3. **`POST /api/face_ou_pile/games/{id}/cancel_game/`**
   - Annule une partie en attente
   - Rembourse la mise au créateur
   - Supprime la partie
   - Réservé au créateur uniquement

4. **`POST /api/face_ou_pile/games/{id}/make_choice/`**
   - Permet au joueur de faire son choix pour la manche actuelle
   - Vérifie que c'est le tour du joueur
   - Enregistre le choix dans `player1_choice`
   - Effectue le tirage aléatoire via `flip_coin()`
   - Termine la manche via `complete_round()`
   - **Envoie un message WebSocket `game_flip_start`** pour synchroniser l'animation
   - Si la partie est terminée : effectue le payout et envoie `game_finished`

**Message WebSocket `game_flip_start` :**
```python
{
    'type': 'game_flip_start',
    'result': game.coin_result,  # 'face' ou 'pile'
    'chooser': game.round_chooser,  # 'player1' ou 'player2'
    'chooser_choice': choice,
    'round': game.current_round,
    'player1_score': game.player1_score,
    'player2_score': game.player2_score,
    'round_winner': round_winner_username,
    'is_game_over': game.status == 'finished',
}
```

**Message WebSocket `game_finished` :**
```python
{
    'type': 'game_finished',
    'winner': game.winner.username,
    'player1_score': game.player1_score,
    'player2_score': game.player2_score,
    'bet_amount': str(game.bet_amount),
}
```

---

### 4. WebSocket Consumer (`consumers.py`)

#### Classe `FaceOuPileGameConsumer`

**Fonctionnalités :**

- **Connexion** : Vérifie l'autorisation (joueur doit être dans la partie)
- **Groupe WebSocket** : `face_ou_pile_{game_id}`
- **Handlers de messages :**
  - `game_flip_start` : Déclenche l'animation de la pièce chez tous les joueurs
  - `game_update` : Mise à jour de l'état du jeu
  - `game_finished` : Notification de fin de partie

**Méthodes :**

- `connect()` : Établit la connexion WebSocket
  - Vérifie l'autorisation via `check_authorization()`
  - Rejoint le groupe WebSocket
  - Envoie l'état initial du jeu

- `check_authorization()` : Vérifie que l'utilisateur est un joueur de la partie
  - Utilise `select_related` pour optimiser les requêtes

- `send_game_state()` : Envoie l'état complet du jeu au groupe
  - Inclut : status, joueurs, scores, manche actuelle, chooser, résultats

- `game_flip_start()` : Broadcast le début de l'animation
  - Transmet : result, chooser, choice, round, scores, round_winner, is_game_over

- `game_update()` : Broadcast les mises à jour du jeu

- `game_finished()` : Broadcast la fin de partie
  - Transmet : winner, scores, bet_amount

---

### 5. WebSocket Routing (`routing.py`)

**Pattern URL :**
```python
websocket_urlpatterns = [
    re_path(r'ws/face_ou_pile/(?P<game_id>[^/]+)/$', consumers.FaceOuPileGameConsumer.as_asgi()),
]
```

**Intégration ASGI :**
- Ajouté dans `projet_casino/asgi.py`
- Routé via `AuthMiddlewareStack`
- Concaténé avec les autres WebSockets (checkers, ludo)

---

## Architecture Frontend

### Template (`game.html`)

#### Structure HTML

**Composants principaux :**

1. **Header** : Bouton retour, affichage du solde
2. **Carte adversaire** : Avatar, nom, statut
3. **Arena centrale** :
   - Affichage du pot
   - Scoreboard BO3 (points, manche actuelle)
   - Pièce 3D (coin-container)
   - Texte de statut
4. **Carte joueur** : Avatar, nom, statut
5. **Action Dock** : Boutons FACE/PILE
6. **Menu Overlay** : Création de partie, liste des parties
7. **Modal Résultat** : Affichage victoire/défaite
8. **Animation Toss Manche 3** : Overlay pour le tirage au sort
9. **Toast Victoire Manche** : Notification de victoire de manche

#### CSS

**Pièce 3D :**
```css
.coin-container {
    width: 8rem;
    height: 8rem;
    perspective: 1000px;
}

.coin {
    transform-style: preserve-3d;
    transition: transform 0.1s;
}

.coin.flipping-face {
    animation: coinFlipFace 3s ease-out forwards;
}

.coin.flipping-pile {
    animation: coinFlipPile 3s ease-out forwards;
}

@keyframes coinFlipFace {
    0% { transform: rotateY(0deg); }
    100% { transform: rotateY(1800deg); }  # Termine sur FACE
}

@keyframes coinFlipPile {
    0% { transform: rotateY(0deg); }
    100% { transform: rotateY(1980deg); }  # Termine sur PILE
}
```

**Faces de la pièce :**
- `coin-front` : FACE (gradient doré clair)
- `coin-back` : PILE (gradient doré foncé, rotateY(180deg))
- `backface-visibility: hidden` pour le rendu 3D correct

**Scoreboard BO3 :**
- 2 points par joueur (dots)
- Indicateur de manche actuelle
- Labels avec initiales des joueurs

**Animations :**
- `pulse` : Animation du texte toss manche 3
- `round-winner-toast` : Slide-in avec bounce effect
- `toss-animation` : Overlay avec backdrop-filter

#### JavaScript

**Variables d'état :**
```javascript
let currentGameId = null;
let pollingInterval = null;
let currentUsername = null;
let isFlipping = false;
let resultModalShown = false;
let selectedChoice = null;
let websocket = null;
let previousRound = 1;
```

**Fonctions principales :**

1. **Gestion WebSocket :**
   - `connectWebSocket()` : Connexion au WebSocket
   - `disconnectWebSocket()` : Déconnexion
   - `handleWebSocketMessage(data)` : Dispatch des messages

2. **Handlers WebSocket :**
   - `handleCoinFlipAnimation(data)` : Séquencement de l'animation
   - `handleGameFinished(data)` : Affichage modal finale
   - `handleGameUpdate(data)` : Mise à jour état jeu

3. **Séquencement de l'animation (`handleCoinFlipAnimation`) :**
   ```
   Étape 1: Animation de la pièce (3s)
   - Ajoute classe CSS selon résultat (flipping-face ou flipping-pile)
   
   Étape 2: Attente visuelle (1.5s)
   - La pièce est stabilisée sur le résultat
   
   Étape 3: Toast victoire manche (2s)
   - Affiche "Manche X remportée par [Joueur] !"
   
   Étape 4: Mise à jour scoreboard
   - Met à jour les points et la manche
   
   Étape 5: Vérification fin de partie
   - Si is_game_over : modal finale via WebSocket
   - Sinon : préparation manche suivante
   ```

4. **Animation Toss Manche 3 (`showRound3Toss`) :**
   - Affiche "Tirage au sort pour la manche décisive..." (1.5s)
   - Affiche "[Joueur] a remporté le tirage et va choisir !" (3s)
   - Masque l'overlay

5. **Gestion de jeu :**
   - `createGame()` : Création d'une partie
   - `joinGame()` : Rejoint une partie existante
   - `sendChoice(choice)` : Envoie le choix à l'API
   - `fetchGame()` : Récupère l'état du jeu (polling)
   - `updateGamePanel(game)` : Met à jour l'UI
   - `updateScoreboard(game)` : Met à jour le scoreboard

6. **Utilitaires :**
   - `apiRequest()` : Wrapper pour fetch avec CSRF
   - `refreshBalance()` : Rafraîchit le solde
   - `fetchCurrentUser()` : Récupère l'utilisateur actuel

**Event Listeners :**
- Bouton retour → `exitGameMode()`
- Créer partie → `createGame()`
- Liste parties → `listGames()`
- Boutons FACE/PILE → `sendChoice()`
- Modal résultat → `closeResultModal()`

---

## Flux de jeu

### 1. Création de partie
```
Joueur 1 → POST /create_game/
  ↓
Déduction mise wallet
  ↓
Création jeu (status: waiting, round: 1, chooser: player1)
  ↓
Retour jeu créé
  ↓
Connexion WebSocket
  ↓
Affichage mode jeu (pot, scoreboard, boutons)
```

### 2. Rejointement de partie
```
Joueur 2 → POST /join_game/
  ↓
Vérification solde
  ↓
Déduction mise wallet
  ↓
Mise à jour jeu (player2, status: playing)
  ↓
Connexion WebSocket J2
  ↓
Broadcast état jeu aux deux joueurs
```

### 3. Déroulement d'une manche
```
Tour du chooser (ex: player1)
  ↓
Clic sur FACE/PILE → POST /make_choice/
  ↓
Vérification tour du joueur
  ↓
Enregistrement choix (player1_choice)
  ↓
Tirage aléatoire (flip_coin)
  ↓
Terminaison manche (complete_round)
  ↓
Calcul gagnant manche
  ↓
Mise à jour scores
  ↓
Broadcast WebSocket game_flip_start
  ↓
Réception chez les deux joueurs
  ↓
Animation synchronisée (3s)
  ↓
Toast victoire manche (2s)
  ↓
Mise à jour scoreboard
  ↓
Si score < 2 → Manche suivante
Si score >= 2 → Fin de partie
```

### 4. Fin de partie
```
Score atteint 2
  ↓
Status: finished
  ↓
Payout (95% du pot)
  ↓
Broadcast WebSocket game_finished
  ↓
Modal victoire/défaite
  ↓
Retour au menu
```

### 5. Manche 3 (Tirage au sort)
```
Score 1-1 après manche 2
  ↓
Transition manche 3
  ↓
Détection updateGamePanel (round: 3, previousRound: 2)
  ↓
showRound3Toss()
  ↓
Overlay "Tirage au sort..." (1.5s)
  ↓
Overlay "[Joueur] a remporté le tirage..." (3s)
  ↓
Masquer overlay
  ↓
Boutons activés pour le chooser
```

---

## WebSocket & Synchronisation

### Architecture WebSocket

**Protocole :** WS/WSS selon le protocole HTTP

**URL :** `ws://host/ws/face_ou_pile/{game_id}/`

**Groupe :** `face_ou_pile_{game_id}`

**Middleware :** `AuthMiddlewareStack` (authentification Django)

### Types de messages

1. **`game_flip_start`** : Déclenchement animation
   - Envoyé par l'API après `make_choice`
   - Reçu par tous les joueurs connectés
   - Déclenche l'animation synchronisée

2. **`game_update`** : Mise à jour état
   - Envoyé par le consumer lors de la connexion
   - Contient l'état complet du jeu

3. **`game_finished`** : Fin de partie
   - Envoyé par l'API après payout
   - Contient le gagnant et les gains

### Synchronisation

**Avant WebSocket :**
- Animation locale uniquement chez le chooser
- Pas de synchronisation entre joueurs

**Après WebSocket :**
- Animation déclenchée simultanément chez les deux joueurs
- Résultat serveur comme source de vérité
- Scores mis à jour de manière cohérente
- Modal finale affichée au bon moment

---

## Animations & UI

### Animation de la pièce

**Rendu 3D CSS :**
- `transform-style: preserve-3d`
- `perspective: 1000px` sur le container
- `backface-visibility: hidden` sur les faces

**Animations distinctes :**
- `coinFlipFace` : 1800° (termine sur 0° = FACE)
- `coinFlipPile` : 1980° (termine sur 180° = PILE)
- Durée : 3 secondes
- Easing : `ease-out`

**Séquencement :**
1. Ajout classe CSS selon résultat serveur
2. Animation 3s
3. Retrait classe (pièce stabilisée)
4. Attente visuelle 1.5s
5. Toast victoire 2s
6. Mise à jour scores

### Toast victoire manche

**Style :**
- Gradient doré (#ffd966 → #ff9500)
- Position fixe (top: 20%)
- Animation slide-in avec bounce
- Durée affichage : 2 secondes

**Contenu :**
- "Manche X remportée par [Joueur] !"
- "Vous" si le joueur actuel est le gagnant

### Animation Toss Manche 3

**Overlay :**
- Fond semi-transparent (rgba(0,0,0,0.85))
- Backdrop-filter blur
- Z-index 150

**Séquencement :**
1. "Tirage au sort pour la manche décisive..." (1.5s)
2. "[Joueur] a remporté le tirage et va choisir !" (3s)
3. Masquer overlay

### Scoreboard BO3

**Affichage :**
- 2 dots par joueur (remplis/vides)
- Labels avec initiales (2 premiers caractères)
- Indicateur de manche actuelle
- "Manche Décisive 3/3" pour la manche 3

**Mise à jour :**
- Synchronisé avec les scores serveur
- Mis à jour après chaque manche
- Affichage en temps réel

---

## Points d'amélioration potentiels

### Backend

1. **Validation des données :**
   - Ajouter des validators pour les montants de mise
   - Limiter le montant maximum de mise
   - Vérifier que le joueur n'a pas de parties en cours

2. **Performance :**
   - Ajouter des indexes sur les champs fréquemment query
   - Utiliser `select_related` systématiquement
   - Implémenter du caching pour les parties actives

3. **Sécurité :**
   - Ajouter rate limiting sur les endpoints
   - Implémenter la vérification CSRF plus strictement
   - Ajouter des logs d'audit

4. **Gestion des erreurs :**
   - Améliorer les messages d'erreur
   - Ajouter des codes d'erreur spécifiques
   - Implémenter un système de retry pour les WebSocket

### Frontend

1. **Expérience utilisateur :**
   - Ajouter des sons pour les animations
   - Implémenter des haptics sur mobile
   - Ajouter un indicateur de connexion WebSocket

2. **Robustesse :**
   - Gérer les reconnexions WebSocket automatiques
   - Ajouter un timeout pour les requêtes API
   - Implémenter un mode offline

3. **Accessibilité :**
   - Ajouter des ARIA labels
   - Supporter le clavier pour les boutons
   - Ajouter un mode contraste élevé

4. **Performance :**
   - Lazy loading des assets
   - Optimiser les animations CSS
   - Réduire la taille du bundle JS

### Architecture

1. **Scalabilité :**
   - Passer à Redis pour les channels layers
   - Implémenter un load balancer pour les WebSocket
   - Ajouter de la redondance

2. **Monitoring :**
   - Ajouter des métriques de performance
   - Implémenter le logging structuré
   - Ajouter des alertes pour les erreurs

3. **Testing :**
   - Ajouter des tests unitaires pour le modèle
   - Ajouter des tests d'intégration pour l'API
   - Ajouter des tests E2E pour le frontend

---

## Conclusion

Le jeu Face ou Pile BO3 est une implémentation complète et fonctionnelle avec :

- ✅ Architecture backend solide (Django REST Framework)
- ✅ Synchronisation temps réel (Django Channels)
- ✅ Frontend réactif avec animations 3D
- ✅ Logique BO3 correcte (scores, manches, alternance)
- ✅ Gestion des mises et des gains
- ✅ Séquencement d'animations soigné

Le code est bien structuré, maintenable et suit les bonnes pratiques Django. Les améliorations suggérées visent à renforcer la robustesse, la performance et l'expérience utilisateur.
