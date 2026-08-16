from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction, models
from django.utils import timezone
from decimal import Decimal
from .models import Game, GameTransaction
from casino_app.wallet.models import Wallet


@login_required
def lobby(request):
    """Vue du lobby public montrant les parties en attente et les parties en cours"""
    waiting_games = Game.objects.filter(status='waiting').order_by('-created_at')
    
    # Ajouter les parties actives où l'utilisateur est un joueur
    active_games = Game.objects.filter(
        status='active'
    ).filter(
        models.Q(player1=request.user) | models.Q(player2=request.user)
    ).order_by('-updated_at')
    
    context = {
        'waiting_games': waiting_games,
        'active_games': active_games,
        'user_wallet': Wallet.objects.get_or_create(utilisateur=request.user)[0]
    }
    return render(request, 'checkers/lobby.html', context)


@login_required
@require_POST
def create_game(request):
    """Créer une nouvelle partie avec mise"""
    stake_amount = request.POST.get('stake')
    
    if not stake_amount:
        messages.error(request, 'Veuillez spécifier une mise')
        return redirect('checkers:lobby')
    
    try:
        stake = Decimal(stake_amount)
        if stake <= 0:
            raise ValueError('La mise doit être positive')
    except (ValueError, TypeError):
        messages.error(request, 'Mise invalide')
        return redirect('checkers:lobby')
    
    # Vérifier le solde du joueur
    wallet = Wallet.objects.get_or_create(utilisateur=request.user)[0]
    if wallet.balance < stake:
        messages.error(request, 'Solde insuffisant')
        return redirect('checkers:lobby')
    
    try:
        with transaction.atomic():
            # Créer la partie
            game = Game.objects.create(
                player1=request.user,
                stake=stake,
                status='waiting'
            )
            
            # Initialiser le plateau
            game.initialize_board()
            
            # Bloquer les fonds du créateur
            game.lock_funds(request.user, stake)
            
            messages.success(request, f'Partie créée avec une mise de {stake} crédits')
            return redirect('checkers:waiting_room', game_id=game.id)
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la création: {str(e)}')
        return redirect('checkers:lobby')


@login_required
def waiting_room(request, game_id):
    """Page d'attente pour le créateur de la partie"""
    game = get_object_or_404(Game, id=game_id)

    # Vérifier que l'utilisateur est le créateur
    if game.player1 != request.user:
        messages.error(request, 'Vous n\'êtes pas le créateur de cette partie')
        return redirect('checkers:lobby')

    # Si la partie est déjà active ou annulée, rediriger
    if game.status == 'active':
        return redirect('checkers:game', game_id=game.id)
    elif game.status == 'cancelled':
        messages.info(request, 'Cette partie a été annulée')
        return redirect('checkers:lobby')

    context = {
        'game': game,
        'game_id': game.id
    }
    return render(request, 'checkers/waiting_room.html', context)


@login_required
@require_POST
def join_game(request, game_id):
    """Rejoindre une partie en attente"""
    game = get_object_or_404(Game, id=game_id, status='waiting')
    
    # Vérifier que le joueur n'est pas déjà dans la partie
    if game.player1 == request.user:
        messages.error(request, 'Vous ne pouvez pas rejoindre votre propre partie')
        return redirect('checkers:lobby')
    
    # Vérifier le solde du joueur
    wallet = Wallet.objects.get_or_create(utilisateur=request.user)[0]
    if wallet.balance < game.stake:
        messages.error(request, 'Solde insuffisant pour rejoindre cette partie')
        return redirect('checkers:lobby')
    
    try:
        with transaction.atomic():
            # Assigner le joueur 2
            game.player2 = request.user
            game.status = 'active'
            game.save()
            
            # Bloquer les fonds du joueur 2
            game.lock_funds(request.user, game.stake)
            
            messages.success(request, 'Partie rejointe avec succès!')
            return redirect('checkers:game', game_id=game.id)
            
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'adhésion: {str(e)}')
        return redirect('checkers:lobby')


@login_required
def game_view(request, game_id):
    """Vue d'une partie active"""
    game = get_object_or_404(Game, id=game_id)

    # Initialize board if empty
    if not game.board_state:
        game.initialize_board()
        game.refresh_from_db()

    # Vérifier que l'utilisateur est un joueur de la partie
    if game.player1 != request.user and game.player2 != request.user:
        messages.error(request, 'Vous n\'êtes pas autorisé à voir cette partie')
        return redirect('checkers:lobby')

    # Si la partie est toujours en attente, rediriger vers le lobby
    if game.status == 'waiting':
        return redirect('checkers:lobby')

    context = {
        'game': game,
        'is_player1': game.player1 == request.user,
        'is_player_turn': game.is_player_turn(request.user)
    }
    return render(request, 'checkers/game.html', context)


@login_required
def game_test(request):
    """Vue de test isolée pour le plateau"""
    return render(request, 'checkers/game_test.html')


@login_required
@require_POST
def cancel_game(request, game_id):
    """Annuler une partie en attente (seul le créateur peut le faire)"""
    game = get_object_or_404(Game, id=game_id, status='waiting')
    
    if game.player1 != request.user:
        messages.error(request, 'Seul le créateur peut annuler la partie')
        return redirect('checkers:lobby')
    
    try:
        with transaction.atomic():
            # Rembourser les fonds bloqués
            game.refund_all_funds()
            
            # Marquer la partie comme annulée
            game.status = 'cancelled'
            game.save()
            
            messages.success(request, 'Partie annulée et fonds remboursés')
            
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'annulation: {str(e)}')
    
    return redirect('checkers:lobby')


@login_required
def api_game_state(request, game_id):
    """API pour récupérer l'état du jeu (pour WebSocket fallback)"""
    game = get_object_or_404(Game, id=game_id)

    # Vérifier que l'utilisateur est un joueur de la partie
    if game.player1 != request.user and game.player2 != request.user:
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    return JsonResponse({
        'game_id': str(game.id),
        'status': game.status,
        'board_state': game.board_state,
        'current_turn': game.current_turn,
        'player1': game.player1.username,
        'player2': game.player2.username if game.player2 else None,
        'winner': game.winner.username if game.winner else None,
        'last_move_at': game.last_move_at.isoformat() if game.last_move_at else None,
        'is_my_turn': game.is_player_turn(request.user)
    })


@login_required
@require_POST
def make_move(request, game_id):
    """API pour exécuter un mouvement"""
    import json
    from django.views.decorators.csrf import csrf_exempt

    game = get_object_or_404(Game, id=game_id, status='active')

    # Vérifier que l'utilisateur est un joueur de la partie
    if game.player1 != request.user and game.player2 != request.user:
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    # Vérifier que c'est le tour du joueur
    if not game.is_player_turn(request.user):
        return JsonResponse({'error': 'Ce n\'est pas votre tour'}, status=400)

    try:
        data = json.loads(request.body)
        from_pos = data.get('from')
        to_pos = data.get('to')

        if not from_pos or not to_pos:
            return JsonResponse({'error': 'Positions manquantes'}, status=400)

        # Valider le mouvement
        is_valid = is_valid_move(game, from_pos, to_pos, request.user)
        
        if not is_valid:
            return JsonResponse({'error': 'Mouvement invalide'}, status=400)

        # Exécuter le mouvement
        execute_move(game, from_pos, to_pos, request.user)

        return JsonResponse({'success': True, 'board_state': game.board_state})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Données invalides'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def forfeit_game(request, game_id):
    """API pour abandonner une partie"""
    try:
        game = Game.objects.get(id=game_id, status='active')
    except Game.DoesNotExist:
        return JsonResponse({'error': 'Game not found or not active'}, status=404)

    # Vérifier que l'utilisateur est un joueur de la partie
    if game.player1 != request.user and game.player2 != request.user:
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    try:
        with transaction.atomic():
            # L'autre joueur gagne
            if game.player1 == request.user:
                game.winner = game.player2
                loser = game.player1
            else:
                game.winner = game.player1
                loser = game.player2

            game.status = 'finished'
            game.save()

            # Libérer les fonds au gagnant
            game.release_funds_to_winner()

            # Récupérer les soldes avant/après
            winner_balance = game.winner.wallet.balance
            loser_balance = loser.wallet.balance

        return JsonResponse({
            'success': True,
            'winner': game.winner.username,
            'loser': loser.username,
            'stake': str(game.stake),
            'winner_balance': str(winner_balance),
            'loser_balance': str(loser_balance),
            'is_winner': request.user == game.winner
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def is_valid_move(game, from_pos, to_pos, user):
    """Valide un mouvement selon les règles des dames internationales"""
    board = game.board_state
    if not board:
        return False

    # Vérifier que la position de départ contient un pion du joueur
    piece = board.get(from_pos)
    if not piece:
        return False

    is_player1 = game.player1 == user
    player_color = 'b' if is_player1 else 'w'

    if piece.lower() != player_color:
        return False

    # Parser les positions
    from_row = int(from_pos[0])
    from_col = int(from_pos[1])
    to_row = int(to_pos[0])
    to_col = int(to_pos[1])

    # Vérifier que la destination est dans le plateau
    if not (0 <= to_row < 10 and 0 <= to_col < 10):
        return False

    # Vérifier que la destination est vide
    if board.get(to_pos) is not None:
        return False

    # Vérifier que c'est une case noire
    if (to_row + to_col) % 2 == 0:
        return False

    # Calculer la distance
    row_diff = to_row - from_row
    col_diff = to_col - from_col
    abs_row_diff = abs(row_diff)
    abs_col_diff = abs(col_diff)

    # Vérifier s'il y a une capture obligatoire
    has_mandatory = has_mandatory_capture(game, user)
    
    # Essayer de trouver un chemin de capture
    capture_path = get_capture_path(board, from_pos, to_pos, piece, player_color)
    is_capture = capture_path is not None
    
    if has_mandatory:
        # Si capture obligatoire, le mouvement doit être une capture
        if not is_capture:
            return False
        
        # Vérifier que c'est le maximum de captures pour TOUS les pions du joueur
        path_captures = (len(capture_path) - 1) // 2
        max_captures_global = get_max_captures_for_color(board, player_color)
        
        if path_captures < max_captures_global:
            return False
        
        return True
    
    # Pas de capture obligatoire
    if is_capture:
        # Capture volontaire - vérifier que c'est valide
        return True
    
    # Mouvement simple (1 case diagonale)
    if abs_row_diff == 1 and abs_col_diff == 1:
        # Vérifier la direction pour les pions non-dames
        is_king = piece == 'B' or piece == 'W'
        if not is_king:
            if player_color == 'b' and row_diff > 0:  # Black doit avancer vers le haut (row diminue)
                return False
            if player_color == 'w' and row_diff < 0:  # White doit avancer vers le bas (row augmente)
                return False
        return True
    
    # Mouvement de dame (plusieurs cases diagonales)
    is_king = piece == 'B' or piece == 'W'
    if is_king and abs_row_diff == abs_col_diff and abs_row_diff > 1:
        # Vérifier que le chemin est libre
        dr = 1 if row_diff > 0 else -1
        dc = 1 if col_diff > 0 else -1
        for i in range(1, abs_row_diff):
            check_row = from_row + i * dr
            check_col = from_col + i * dc
            check_pos = f"{check_row}{check_col}"
            if board.get(check_pos) is not None:
                return False
        return True
    
    return False


def calculate_max_captures(board, position, piece, player_color, visited=None):
    """Calcule le nombre maximum de pions qui peuvent être capturés depuis une position"""
    if visited is None:
        visited = set()
    
    if position in visited:
        return 0
    
    visited.add(position)
    row = int(position[0])
    col = int(position[1])
    is_king = piece == 'B' or piece == 'W'
    
    max_captures = 0
    
    if is_king:
        # Dame volante: peut capturer à distance sur les diagonales
        directions = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
        
        for dr, dc in directions:
            # Chercher des pièces adverses sur cette diagonale
            found_enemy = None
            enemy_pos = None
            
            for i in range(1, 10):
                check_row = row + i * dr
                check_col = col + i * dc
                
                if not (0 <= check_row < 10 and 0 <= check_col < 10):
                    break
                
                check_pos = f"{check_row}{check_col}"
                check_piece = board.get(check_pos)
                
                if check_piece:
                    if check_piece.lower() != player_color:
                        # Pièce adverse trouvée
                        found_enemy = check_piece
                        enemy_pos = check_pos
                        break
                    else:
                        # Pièce alliée, chemin bloqué
                        break
            
            if found_enemy:
                # Chercher les positions d'atterrissage après la pièce adverse
                for i in range(1, 10):
                    land_row = int(enemy_pos[0]) + i * dr
                    land_col = int(enemy_pos[1]) + i * dc
                    
                    if not (0 <= land_row < 10 and 0 <= land_col < 10):
                        break
                    
                    land_pos = f"{land_row}{land_col}"
                    
                    # Vérifier que la position d'atterrissage est vide
                    if board.get(land_pos) is not None:
                        break
                    
                    # Simuler la capture
                    temp_board = board.copy()
                    temp_board[enemy_pos] = None
                    temp_board[land_pos] = piece
                    temp_board[position] = None
                    
                    # Calculer les captures supplémentaires depuis la nouvelle position
                    additional_captures = calculate_max_captures(temp_board, land_pos, piece, player_color, visited.copy())
                    total_captures = 1 + additional_captures
                    
                    if total_captures > max_captures:
                        max_captures = total_captures
    else:
        # Pion: capture à 2 cases seulement
        directions = [[-2, -2], [-2, 2], [2, -2], [2, 2]]
        
        for dr, dc in directions:
            new_row = row + dr
            new_col = col + dc
            mid_row = row + dr // 2
            mid_col = col + dc // 2
            
            # Vérifier que la destination est dans le plateau
            if not (0 <= new_row < 10 and 0 <= new_col < 10):
                continue
            
            new_pos = f"{new_row}{new_col}"
            mid_pos = f"{mid_row}{mid_col}"
            
            # Vérifier que la destination est vide
            if board.get(new_pos) is not None:
                continue
            
            # Vérifier qu'il y a un pion adverse au milieu
            mid_piece = board.get(mid_pos)
            if mid_piece and mid_piece.lower() != player_color:
                # Simuler la capture
                temp_board = board.copy()
                temp_board[mid_pos] = None
                
                # Vérifier si le pion est promu après ce mouvement
                new_piece = piece
                is_promoted = False
                if piece == 'w' and new_row == 9:
                    new_piece = 'W'
                    is_promoted = True
                elif piece == 'b' and new_row == 0:
                    new_piece = 'B'
                    is_promoted = True
                
                temp_board[new_pos] = new_piece
                temp_board[position] = None
                
                # Si le pion est promu, la capture s'arrête (règle internationale)
                if is_promoted:
                    total_captures = 1
                else:
                    # Calculer les captures supplémentaires depuis la nouvelle position
                    additional_captures = calculate_max_captures(temp_board, new_pos, new_piece, player_color, visited.copy())
                    total_captures = 1 + additional_captures
                
                if total_captures > max_captures:
                    max_captures = total_captures
    
    return max_captures


def get_capture_path(board, from_pos, to_pos, piece, player_color, visited=None):
    """Calcule le chemin de capture entre deux positions de manière récursive"""
    if visited is None:
        visited = set()
    
    if from_pos in visited:
        return None
    
    visited.add(from_pos)
    row = int(from_pos[0])
    col = int(from_pos[1])
    is_king = piece == 'B' or piece == 'W'
    
    # Si on est déjà à la destination
    if from_pos == to_pos:
        return [from_pos]
    
    if is_king:
        # Dame volante: peut capturer à distance sur les diagonales
        directions = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
        
        for dr, dc in directions:
            # Chercher des pièces adverses sur cette diagonale
            found_enemy = None
            enemy_pos = None
            
            for i in range(1, 10):
                check_row = row + i * dr
                check_col = col + i * dc
                
                if not (0 <= check_row < 10 and 0 <= check_col < 10):
                    break
                
                check_pos = f"{check_row}{check_col}"
                check_piece = board.get(check_pos)
                
                if check_piece:
                    if check_piece.lower() != player_color:
                        # Pièce adverse trouvée
                        found_enemy = check_piece
                        enemy_pos = check_pos
                        break
                    else:
                        # Pièce alliée, chemin bloqué
                        break
            
            if found_enemy:
                # Chercher les positions d'atterrissage après la pièce adverse
                for i in range(1, 10):
                    land_row = int(enemy_pos[0]) + i * dr
                    land_col = int(enemy_pos[1]) + i * dc
                    
                    if not (0 <= land_row < 10 and 0 <= land_col < 10):
                        break
                    
                    land_pos = f"{land_row}{land_col}"
                    
                    # Vérifier que la position d'atterrissage est vide
                    if board.get(land_pos) is not None:
                        break
                    
                    # Simuler la capture
                    temp_board = board.copy()
                    temp_board[enemy_pos] = None
                    temp_board[land_pos] = piece
                    temp_board[from_pos] = None
                    
                    # Si land_pos est la destination finale
                    if land_pos == to_pos:
                        return [from_pos, enemy_pos, to_pos]
                    
                    # Chercher récursivement le chemin depuis land_pos
                    sub_path = get_capture_path(temp_board, land_pos, to_pos, piece, player_color, visited.copy())
                    
                    if sub_path:
                        return [from_pos, enemy_pos, land_pos] + sub_path[1:]
    else:
        # Pion: capture à 2 cases seulement
        directions = [[-2, -2], [-2, 2], [2, -2], [2, 2]]
        
        for dr, dc in directions:
            new_row = row + dr
            new_col = col + dc
            mid_row = row + dr // 2
            mid_col = col + dc // 2
            
            # Vérifier que la destination est dans le plateau
            if not (0 <= new_row < 10 and 0 <= new_col < 10):
                continue
            
            new_pos = f"{new_row}{new_col}"
            mid_pos = f"{mid_row}{mid_col}"
            
            # Vérifier que la destination est vide
            if board.get(new_pos) is not None:
                continue
            
            # Vérifier qu'il y a un pion adverse au milieu
            mid_piece = board.get(mid_pos)
            if mid_piece and mid_piece.lower() != player_color:
                # Simuler la capture
                temp_board = board.copy()
                temp_board[mid_pos] = None
                
                # Vérifier si le pion est promu après ce mouvement
                new_piece = piece
                is_promoted = False
                if piece == 'w' and new_row == 9:
                    new_piece = 'W'
                    is_promoted = True
                elif piece == 'b' and new_row == 0:
                    new_piece = 'B'
                    is_promoted = True
                
                temp_board[new_pos] = new_piece
                temp_board[from_pos] = None
                
                # Si new_pos est la destination finale
                if new_pos == to_pos:
                    return [from_pos, mid_pos, to_pos]
                
                # Si le pion est promu, la capture s'arrête (règle internationale)
                if is_promoted:
                    continue
                
                # Chercher récursivement le chemin depuis new_pos
                sub_path = get_capture_path(temp_board, new_pos, to_pos, new_piece, player_color, visited.copy())
                
                if sub_path:
                    return [from_pos, mid_pos, new_pos] + sub_path[1:]
    
    return None


def get_max_captures_for_color(board, player_color):
    """Retourne le nombre maximum de pions capturables pour une couleur"""
    if not board:
        return 0
    
    max_captures = 0
    
    for pos, piece in board.items():
        if piece and piece.lower() == player_color:
            captures = calculate_max_captures(board, pos, piece, player_color)
            if captures > max_captures:
                max_captures = captures
    
    return max_captures


def get_max_captures_for_player(game, user):
    """Retourne le nombre maximum de pions capturables pour un joueur"""
    board = game.board_state
    if not board:
        return 0
    
    is_player1 = game.player1 == user
    player_color = 'b' if is_player1 else 'w'
    
    return get_max_captures_for_color(board, player_color)


def has_mandatory_capture(game, user):
    """Vérifie si le joueur a une capture obligatoire disponible"""
    board = game.board_state
    if not board:
        return False

    is_player1 = game.player1 == user
    player_color = 'b' if is_player1 else 'w'

    # Parcourir tous les pions du joueur
    for pos, piece in board.items():
        if piece and piece.lower() == player_color:
            captures = calculate_max_captures(board, pos, piece, player_color)
            if captures > 0:
                return True  # Capture obligatoire trouvée

    return False


def execute_move(game, from_pos, to_pos, user):
    """Exécute un mouvement et met à jour le plateau"""
    board = game.board_state.copy()
    piece = board[from_pos]
    
    is_player1 = game.player1 == user
    player_color = 'b' if is_player1 else 'w'

    #  IMPORTANT : on cherche TOUJOURS un chemin de capture
    capture_path = get_capture_path(board, from_pos, to_pos, piece, player_color)

    if capture_path:
        #  Multi OU simple capture (unifié)
        # Parcourir le chemin de capture et s'arrêter si une promotion se produit
        current_piece = piece
        current_pos = from_pos
        
        for i in range(1, len(capture_path), 2):
            if i + 1 < len(capture_path):
                mid_pos = capture_path[i]
                land_pos = capture_path[i + 1]
                
                # Supprimer le pion capturé
                board[mid_pos] = None
                
                # Déplacer la pièce
                board[land_pos] = current_piece
                board[current_pos] = None
                
                # Vérifier si le pion est promu après ce saut
                land_row = int(land_pos[0])
                is_promoted = False
                if current_piece == 'w' and land_row == 9:
                    current_piece = 'W'
                    board[land_pos] = 'W'
                    is_promoted = True
                elif current_piece == 'b' and land_row == 0:
                    current_piece = 'B'
                    board[land_pos] = 'B'
                    is_promoted = True
                
                current_pos = land_pos
                
                # Si le pion est promu, la capture s'arrête (règle internationale)
                if is_promoted:
                    break

    else:
        #  mouvement simple
        board[to_pos] = piece
        board[from_pos] = None

        #  promotion pour mouvement simple
        to_row = int(to_pos[0])
        if piece == 'w' and to_row == 9:
            board[to_pos] = 'W'
        elif piece == 'b' and to_row == 0:
            board[to_pos] = 'B'

    game.board_state = board
    game.last_move_at = timezone.now()
    game.current_turn = 2 if game.current_turn == 1 else 1

    check_game_over(game)
    game.save()


def check_game_over(game):
    """Vérifie si la partie est terminée"""
    board = game.board_state
    if not board:
        return

    # Compter les pions de chaque joueur
    black_count = 0
    white_count = 0

    for pos, piece in board.items():
        if piece:
            if piece.lower() == 'b':
                black_count += 1
            elif piece.lower() == 'w':
                white_count += 1

    # Vérifier si un joueur n'a plus de pions
    if black_count == 0:
        game.status = 'finished'
        game.winner = game.player2
    elif white_count == 0:
        game.status = 'finished'
        game.winner = game.player1
    else:
        # Vérifier si le joueur actuel a des mouvements possibles
        current_player = game.player1 if game.current_turn == 1 else game.player2
        if not has_valid_moves(game, current_player):
            game.status = 'finished'
            game.winner = game.player2 if game.current_turn == 1 else game.player1


def has_valid_moves(game, user):
    """Vérifie si le joueur a des mouvements valides"""
    board = game.board_state
    if not board:
        return False

    is_player1 = game.player1 == user
    player_color = 'b' if is_player1 else 'w'

    # Parcourir tous les pions du joueur
    for pos, piece in board.items():
        if piece and piece.lower() == player_color:
            row = int(pos[0])
            col = int(pos[1])
            is_king = piece == 'B' or piece == 'W'

            # Vérifier les mouvements simples
            if is_king:
                # Dame volante: peut se déplacer sur plusieurs cases diagonales
                directions = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
                for dr, dc in directions:
                    for i in range(1, 10):
                        new_row = row + i * dr
                        new_col = col + i * dc
                        if not (0 <= new_row < 10 and 0 <= new_col < 10):
                            break
                        new_pos = f"{new_row}{new_col}"
                        if board.get(new_pos) is not None:
                            break
                        return True
            else:
                # Pion: mouvement simple sur 1 case diagonale
                directions = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
                for dr, dc in directions:
                    # Vérifier la direction pour les pions non-dames
                    if player_color == 'b' and dr > 0:
                        continue
                    if player_color == 'w' and dr < 0:
                        continue

                    new_row = row + dr
                    new_col = col + dc

                    if 0 <= new_row < 10 and 0 <= new_col < 10:
                        new_pos = f"{new_row}{new_col}"
                        if board.get(new_pos) is None:
                            return True

            # Vérifier les captures
            # En dames internationales, les pions peuvent capturer dans toutes les directions
            if is_king:
                # Dame volante: peut capturer à distance
                directions = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
                for dr, dc in directions:
                    # Chercher des pièces adverses sur cette diagonale
                    for i in range(1, 10):
                        check_row = row + i * dr
                        check_col = col + i * dc
                        if not (0 <= check_row < 10 and 0 <= check_col < 10):
                            break
                        check_pos = f"{check_row}{check_col}"
                        check_piece = board.get(check_pos)
                        if check_piece:
                            if check_piece.lower() != player_color:
                                # Pièce adverse trouvée, chercher une case vide après
                                for j in range(1, 10):
                                    land_row = check_row + j * dr
                                    land_col = check_col + j * dc
                                    if not (0 <= land_row < 10 and 0 <= land_col < 10):
                                        break
                                    land_pos = f"{land_row}{land_col}"
                                    if board.get(land_pos) is None:
                                        return True
                                    break
                            else:
                                break
            else:
                # Pion: capture à 2 cases
                capture_directions = [[-2, -2], [-2, 2], [2, -2], [2, 2]]
                for dr, dc in capture_directions:
                    new_row = row + dr
                    new_col = col + dc
                    mid_row = row + dr // 2
                    mid_col = col + dc // 2

                    if 0 <= new_row < 10 and 0 <= new_col < 10:
                        new_pos = f"{new_row}{new_col}"
                        mid_pos = f"{mid_row}{mid_col}"
                        mid_piece = board.get(mid_pos)

                        if board.get(new_pos) is None and mid_piece and mid_piece.lower() != player_color:
                            return True

    return False
