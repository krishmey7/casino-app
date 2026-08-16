from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import RoulettePartie
from casino_app.wallet.models import Wallet


@login_required
def roulett_partie_vue(request):
    portefeuille, _ = Wallet.objects.get_or_create(utilisateur=request.user)
    parties = RoulettePartie.objects.filter(joueur=request.user).order_by('-created_at')[:10]

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Endpoint AJAX pour calcul du résultat + animation
        try:
            data = request.POST
            mise = Decimal(str(data.get('mise', '100.00')))
            numero_pari = int(data.get('numero_pari', '0'))

            if mise <= 0:
                raise ValueError('La mise doit être supérieure à 0')
            if numero_pari < 0 or numero_pari > 36:
                raise ValueError('Le numéro doit être entre 0 et 36')
            if portefeuille.balance < mise:
                raise ValueError('Solde insuffisant')

            portefeuille.debit(mise, description=f'Mise Roulette - {mise}')
            partie = RoulettePartie.objects.create(joueur=request.user, mise=mise)
            result = partie.jouer(numero_pari)

            if partie.statut == 'gagné':
                portefeuille.credit(partie.gain, description=f'Gain Roulette - partie {partie.id}')

            response_data = {
                'numero_pari': partie.numero_pari,
                'numero_tire': partie.numero_tire,
                'statut': partie.statut,
                'gain': float(partie.gain),
                'solde': float(portefeuille.balance),
                'message': result,
                'partie': {
                    'id': str(partie.id),
                    'created_at': partie.created_at.strftime('%d/%m/%Y %H:%M:%S'),
                }
            }
            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    # mode page classique
    contexte = {
        'erreur': None,
        'message': None,
        'partie': None,
        'solde': portefeuille.balance,
        'parties': parties,
    }

    return render(request, 'roulette/game.html', contexte)
