# Lucky Numbers - Jeu de Tirage

## Description
Lucky Numbers est une application de jeu d'hasard basée sur Django où les utilisateurs choisissent un chiffre (0-9), placent un pari, et gagnent 10x leur mise s'ils ont raison !

## Structure

### Modèles
- **LuckyNumberGame**: Représente une partie avec ses états (waiting, playing, finished) et le numéro gagnant
- **LuckyNumberBet**: Représente un pari placé par un utilisateur avec le montant, le chiffre choisi et le statut

### États de Jeu
- `waiting`: Jeu en attente (pas utilisé dans la logique actuelle)
- `playing`: Jeu en cours, les utilisateurs peuvent placer des paris
- `finished`: Jeu terminé, le numéro gagnant a été tiré

### États de Pari
- `pending`: Pari en attente du tirage
- `won`: Pari gagnant (10x la mise)
- `lost`: Pari perdu

## API Endpoints

### Parties
- `GET /api/lucky_numbers/games/current/` - Récupère ou crée la partie actuelle
- `POST /api/lucky_numbers/games/start_new_game/` - Crée une nouvelle partie
- `POST /api/lucky_numbers/games/{id}/draw/` - **IMPORTANT**: Effectue le tirage aléatoire et détermine les gagnants

### Paris
- `POST /api/lucky_numbers/bets/` - Place un nouveau pari
- `GET /api/lucky_numbers/bets/my_bets/` - Récupère les paris de l'utilisateur
- `GET /api/lucky_numbers/bets/game_bets/?game_id={id}` - Récupère tous les paris d'une partie

### Portefeuille
- `GET /api/wallet/balance/` - Récupère le solde de l'utilisateur
- `POST /api/wallet/credit/` - Crédite un compte
- `POST /api/wallet/debit/` - Débite un compte

## Flux du Jeu

1. **Lancer une partie**
   - Créer une nouvelle partie avec `POST /api/lucky_numbers/games/start_new_game/`
   - Ou récupérer la partie actuelle avec `GET /api/lucky_numbers/games/current/`

2. **Placer un pari**
   ```json
   POST /api/lucky_numbers/bets/
   {
       "game": "uuid-du-jeu",
       "chosen_number": 5,
       "bet_amount": "100.00"
   }
   ```
   - Le montant est automatiquement débité du portefeuille
   - Le statut du pari est `pending`

3. **Générer le résultat**
   ```
   POST /api/lucky_numbers/games/{game_id}/draw/
   ```
   - Effectue le tirage aléatoire
   - Détermine les gagnants
   - Crédite les gagnants automatiquement
   - Retourne les résultats

## Intégration avec Wallet

L'application utilise le système de portefeuille existant sans créer de nouvelles tables.

### Transactions Automatiques
- **Placement du pari**: La mise est déduite via `wallet.debit()`
- **Gain**: Les gains sont crédités via `wallet.credit()`
- **Descriptions**: Toutes les transactions sont enregistrées avec une description

### Exemple de Flux Transactionnel
```
1. Solde initial: 1000.00
2. Pari de 100 → Solde: 900.00 (Transaction: Mise)
3. Déroulement du tirage
4. Gagné 10x (1000) → Solde: 1900.00 (Transaction: Gain)
```

## Interface Web

L'interface est accessible à: `http://localhost:8000/lucky_numbers/`

### Fonctionnalités
- 📊 Affichage du solde en temps réel
- 🎲 Grille de 10 chiffres (0-9) pour sélectionner
- 💰 Montant de pari personnalisable
- 🎯 Tirage aléatoire avec bouton
- 📈 Historique des 5 derniers paris
- 📱 Responsive design (desktop et mobile)

## Installation et Migration

1. L'app est déjà enregistrée dans `settings.py`
2. L'app est déjà dans les URLs de `projet_casino`
3. Exécuter les migrations:
   ```
   python manage.py migrate
   ```

## Admin Django

Accueil Admin: `/admin/lucky_numbers/`

### Gestion
- Voir toutes les parties et leurs statuts
- Voir tous les paris d'une partie
- Modifier manuellement les états (si nécessaire)

## Points Importants

⚠️ **SÉCURITÉ**
- Toutes les transactions sont atomiques (ACID)
- Les vérifications de solde sont faites avant de créer le pari
- Les gains sont calculés et crédités après le tirage
- Authentification requise pour tous les endpoints

⚠️ **LOGIQUE DU JEU**
- Un tirage = UN seul numéro (0-9)
- Probabilité de gain: 10% pour chaque pari
- Ratio de gain: 10x la mise
- Pas de cotcôté des gains (directs)

## Dépannage

### Erreurs Courants

**"Insufficient balance"**
- L'utilisateur n'a pas assez d'argent pour cette mise

**"Game not available"**
- La partie n'est pas en état `playing` ou n'existe pas

**"Number must be between 0 and 9"**
- Un numéro invalide a été soumis

### Logs
Vérifier `django.log` pour les traces d'exécution et les erreurs

## Fichiers Clés

- `models.py` - Définition des modèles
- `api_views.py` - Logique des endpoints API
- `serializers.py` - Sérialiseurs DRF
- `api_urls.py` - Routage des endpoints
- `templates/lucky_numbers/game.html` - Interface frontend
- `admin.py` - Configuration Admin Django
