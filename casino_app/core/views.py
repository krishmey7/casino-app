from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages


def affichage_connexion(request):
    """Vue pour la page de connexion"""
    if request.method == 'POST':
        email_or_username = request.POST.get('email')
        password = request.POST.get('password')
        
        # Essayer d'authentifier par nom d'utilisateur d'abord
        user = authenticate(request, username=email_or_username, password=password)
        
        # Si pas trouvé, essayer par email
        if user is None:
            try:
                user_obj = User.objects.get(email=email_or_username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue {user.first_name or user.username}!')
            return redirect('accueil')
        else:
            messages.error(request, 'Email/Nom d\'utilisateur ou mot de passe incorrect')
    
    return render(request, 'core/connexion.html')


def affichage_inscription(request):
    """Vue pour la page d'inscription"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Validations
        if password != password_confirm:
            messages.error(request, 'Les mots de passe ne correspondent pas')
            return render(request, 'core/inscription.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur est déjà pris')
            return render(request, 'core/inscription.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Cet email est déjà utilisé')
            return render(request, 'core/inscription.html')
        
        if len(password) < 8:
            messages.error(request, 'Le mot de passe doit faire au minimum 8 caractères')
            return render(request, 'core/inscription.html')
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Créer le wallet pour l'utilisateur
        from casino_app.wallet.models import Wallet
        Wallet.objects.create(utilisateur=user, balance=1000.00)  # Solde initial de 1000
        
        # Connexion automatique après inscription
        login(request, user)
        messages.success(request, f'Bienvenue {first_name}! Votre compte a été créé avec succès.')
        return redirect('accueil')
    
    return render(request, 'core/inscription.html')


def affichage_deconnexion(request):
    """Vue pour la déconnexion"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté')
    return redirect('accueil')


def jeux(request):
    """Vue pour la page des jeux"""
    
    return render(request, 'core/jeux.html')




def accueil(request):
    """Vue pour la page d'accueil"""
    # Données des jeux pour la section "Nos Jeux"
    games = [
        {
            'name': 'LUDO',
            'players': '2-4',
            'description': 'Jeu de plateau classique multijoueur',
            'url': '/ludo/lobby/',
            'icon': '🎲'
        },
        {
            'name': 'Dames',
            'players': '2',
            'description': 'Jeu de stratégie classique',
            'url': '/checkers/lobby/',
            'icon': '♟️'
        },
        {
            'name': 'Machine à Sous',
            'players': '1',
            'description': 'Tentez votre chance',
            'url': '#',
            'icon': '🎰'
        },
        {
            'name': 'Poker',
            'players': '2-8',
            'description': 'Le roi des jeux de cartes',
            'url': '#',
            'icon': '🃏'
        },
        {
            'name': 'Roulette',
            'players': '1+',
            'description': 'La chance tourne',
            'url': '#',
            'icon': '🎲'
        },
        {
            'name': 'Blackjack',
            'players': '1-7',
            'description': 'Approchez-vous de 21',
            'url': '#',
            'icon': '🃏'
        },
        {
            'name': 'Baccarat',
            'players': '1-8',
            'description': 'Jeu d\'élégance',
            'url': '#',
            'icon': '🎴'
        },
        {
            'name': 'Pierre-Feuille-Ciseaux',
            'players': '2',
            'description': 'Jeu classique multijoueur',
            'url': '/rock_paper_scissors/',
            'icon': '✂️'
        }
    ]
    
    context = {
        'games': games
    }
    
    return render(request, 'core/accueil.html', context)
