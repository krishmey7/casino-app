from django import template

register = template.Library()


@register.filter
def get_color_name(color_code):
    """Retourne le nom de la couleur en français"""
    color_names = {
        'red': 'Rouge',
        'blue': 'Bleu',
        'green': 'Vert',
        'yellow': 'Jaune'
    }
    return color_names.get(color_code, color_code)


@register.filter
def get_color_hex(color_code):
    """Retourne le code hexadécimal de la couleur"""
    color_hex = {
        'red': '#ef4444',
        'blue': '#3b82f6',
        'green': '#22c55e',
        'yellow': '#eab308'
    }
    return color_hex.get(color_code, '#999999')


@register.filter
def is_player_turn(game, player):
    """Vérifie si c'est le tour du joueur"""
    if game.status != 'active':
        return False
    return game.current_turn == player.turn_order


@register.filter
def get_token_position(tokens, index):
    """Retourne la position d'un pion"""
    try:
        return tokens[index]
    except (IndexError, TypeError):
        return -1


@register.filter
def is_token_in_base(position):
    """Vérifie si un pion est dans la base"""
    return position == -1


@register.filter
def is_token_finished(position):
    """Vérifie si un pion est terminé"""
    return position == 61


@register.filter
def is_token_in_home_stretch(position):
    """Vérifie si un pion est dans la zone d'arrivée"""
    return position >= 56 and position < 61


@register.simple_tag
def get_game_status_class(status):
    """Retourne la classe CSS pour le statut de la partie"""
    status_classes = {
        'waiting': 'bg-warning',
        'active': 'bg-success',
        'finished': 'bg-primary',
        'cancelled': 'bg-danger'
    }
    return status_classes.get(status, 'bg-secondary')


@register.simple_tag
def get_player_status_class(is_connected, is_ready):
    """Retourne la classe CSS pour le statut du joueur"""
    if not is_connected:
        return 'bg-danger'
    if is_ready:
        return 'bg-success'
    return 'bg-warning'


@register.filter
def get_game_duration(started_at, finished_at=None):
    """Calcule la durée de la partie"""
    from django.utils import timezone
    
    if not started_at:
        return "Non démarrée"
    
    end = finished_at or timezone.now()
    duration = end - started_at
    
    hours = int(duration.total_seconds() // 3600)
    minutes = int((duration.total_seconds() % 3600) // 60)
    seconds = int(duration.total_seconds() % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
