"""
Vues pour LUDO
Gestion HTTP des parties, lobby et API
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction, models
from django.utils import timezone
from decimal import Decimal
from .models import LudoGame, LudoPlayer
from .services import GameService, GameEngineService
from casino_app.wallet.models import Wallet


@login_required
def lobby(request):
    """Vue du lobby public montrant les parties en attente et les parties en cours"""
    waiting_games = LudoGame.objects.filter(status='waiting').order_by('-created_at')
    
    # Ajouter les parties actives où l'utilisateur est un joueur
    active_games = LudoGame.objects.filter(
        status='active'
    ).filter(
        models.Q(ludoplayers__user=request.user)
    ).distinct().order_by('-updated_at')
    
    context = {
        'waiting_games': waiting_games,
        'active_games': active_games,
        'user_wallet': Wallet.objects.get_or_create(utilisateur=request.user)[0]
    }
    return render(request, 'ludo/lobby.html', context)


@login_required
@require_POST
@transaction.atomic
def create_game(request):
    """Créer une nouvelle partie avec mise et nombre de joueurs minimum"""
    stake_amount = request.POST.get('stake')
    min_players = request.POST.get('min_players', '2')
    
    if not stake_amount:
        messages.error(request, 'Veuillez spécifier une mise')
        return redirect('ludo:lobby')
    
    try:
        stake = Decimal(stake_amount)
        if stake <= 0:
            raise ValueError('La mise doit être positive')
    except (ValueError, TypeError):
        messages.error(request, 'Mise invalide')
        return redirect('ludo:lobby')
    
    try:
        min_players = int(min_players)
        if min_players not in [2, 3, 4]:
            raise ValueError('Le nombre de joueurs doit être 2, 3 ou 4')
    except (ValueError, TypeError):
        messages.error(request, 'Nombre de joueurs invalide')
        return redirect('ludo:lobby')
    
    # Vérifier le solde du wallet
    wallet = Wallet.objects.get_or_create(utilisateur=request.user)[0]
    if wallet.balance < stake:
        messages.error(request, 'Solde insuffisant')
        return redirect('ludo:lobby')
    
    # Créer la partie avec min_players
    game = GameService.create_game(request.user, stake, min_players)
    
    messages.success(request, f'Partie créée avec succès !')
    return redirect('ludo:waiting_room', game_id=game.id)


@login_required
def waiting_room(request, game_id):
    """Vue de la salle d'attente"""
    game = get_object_or_404(LudoGame, id=game_id)
    
    # Vérifier que l'utilisateur est dans la partie
    if not LudoPlayer.objects.filter(game=game, user=request.user).exists():
        messages.error(request, 'Vous n\'êtes pas dans cette partie')
        return redirect('ludo:lobby')
    
    # Récupérer les joueurs
    players = game.ludoplayers.all().order_by('turn_order')
    
    context = {
        'game': game,
        'players': players,
        'current_player': players.filter(user=request.user).first()
    }
    return render(request, 'ludo/waiting_room.html', context)


@login_required
@require_POST
@transaction.atomic
def join_game(request, game_id):
    """Rejoindre une partie existante"""
    game = get_object_or_404(LudoGame, id=game_id)
    
    if game.status != 'waiting':
        messages.error(request, 'Cette partie n\'est plus disponible')
        return redirect('ludo:lobby')
    
    try:
        player = GameService.join_game(game, request.user)
        messages.success(request, 'Vous avez rejoint la partie !')
        return redirect('ludo:waiting_room', game_id=game.id)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('ludo:lobby')


@login_required
@require_POST
@transaction.atomic
def cancel_game(request, game_id):
    """Annuler une partie"""
    game = get_object_or_404(LudoGame, id=game_id)
    
    # Vérifier que l'utilisateur est le créateur (premier joueur)
    first_player = game.ludoplayers.all().order_by('turn_order').first()
    if not first_player or first_player.user != request.user:
        messages.error(request, 'Seul le créateur peut annuler la partie')
        return redirect('ludo:lobby')
    
    if game.status not in ['waiting', 'active']:
        messages.error(request, 'Impossible d\'annuler cette partie')
        return redirect('ludo:lobby')
    
    try:
        GameService.cancel_game(game, request.user)
        messages.success(request, 'Partie annulée')
        return redirect('ludo:lobby')
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('ludo:lobby')


@login_required
def game_view(request, game_id):
    """Vue principale de la partie de jeu"""
    game = get_object_or_404(LudoGame, id=game_id)
    
    # Vérifier que l'utilisateur est dans la partie
    player = LudoPlayer.objects.filter(game=game, user=request.user).first()
    if not player:
        messages.error(request, 'Vous n\'êtes pas dans cette partie')
        return redirect('ludo:lobby')
    
    # Gérer le marquage comme prêt (pour la salle d'attente)
    if request.method == 'POST' and game.status == 'waiting':
        try:
            data = json.loads(request.body)
            if data.get('type') == 'mark_ready':
                player.mark_ready()
                
                # Vérifier si la partie peut démarrer automatiquement
                if game.can_start():
                    GameService.start_game(game)
                
                return JsonResponse({'success': True})
        except (json.JSONDecodeError, KeyError):
            pass
    
    # Si la partie est en attente, rediriger vers la salle d'attente
    if game.status == 'waiting':
        return redirect('ludo:waiting_room', game_id=game.id)
    
    # Récupérer tous les joueurs
    players = list(game.ludoplayers.all().order_by('turn_order'))
    
    # Récupérer le moteur de jeu
    engine = GameEngineService.get_game_engine(game)
    
    # Récupérer les mouvements valides si c'est le tour du joueur
    valid_moves = []
    if game.status == 'active' and game.current_turn == player.turn_order:
        valid_moves = engine.get_valid_moves_for_player(player.color)
    
    context = {
        'game': game,
        'player': player,
        'players': players,
        'valid_moves': valid_moves,
        'game_state': game.game_state,
        'is_current_turn': game.status == 'active' and game.current_turn == player.turn_order
    }
    return render(request, 'ludo/game.html', context)


@login_required
@require_POST
def forfeit_game(request, game_id):
    """Abandonner une partie"""
    game = get_object_or_404(LudoGame, id=game_id)
    
    # Vérifier que l'utilisateur est dans la partie
    if not LudoPlayer.objects.filter(game=game, user=request.user).exists():
        return JsonResponse({'success': False, 'error': 'Vous n\'êtes pas dans cette partie'})
    
    if game.status != 'active':
        return JsonResponse({'success': False, 'error': 'La partie n\'est pas active'})
    
    try:
        GameService.handle_forfeit(game, request.user)
        return JsonResponse({'success': True})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})


# API endpoints

@login_required
def api_game_state(request, game_id):
    """API pour récupérer l'état du jeu"""
    game = get_object_or_404(LudoGame, id=game_id)
    
    # Vérifier que l'utilisateur est dans la partie
    if not LudoPlayer.objects.filter(game=game, user=request.user).exists():
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    players = game.ludoplayers.all().order_by('turn_order')
    
    return JsonResponse({
        'success': True,
        'game': {
            'id': str(game.id),
            'status': game.status,
            'current_turn': game.current_turn,
            'stake': str(game.stake),
            'game_state': game.game_state,
            'winner': game.winner.username if game.winner else None
        },
        'players': [
            {
                'username': player.user.username,
                'color': player.color,
                'turn_order': player.turn_order,
                'is_connected': player.is_connected,
                'is_ready': player.is_ready
            }
            for player in players
        ]
    })


@login_required
def api_valid_moves(request, game_id):
    """API pour récupérer les mouvements valides"""
    game = get_object_or_404(LudoGame, id=game_id)
    
    # Vérifier que l'utilisateur est dans la partie
    player = LudoPlayer.objects.filter(game=game, user=request.user).first()
    if not player:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if game.status != 'active':
        return JsonResponse({'success': False, 'error': 'Game not active'})
    
    # Récupérer les mouvements valides
    engine = GameEngineService.get_game_engine(game)
    valid_moves = engine.get_valid_moves_for_player(player.color)
    
    return JsonResponse({
        'success': True,
        'valid_moves': valid_moves
    })
