"""
URL configuration for casino_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('casino_app.core.urls')),
    path('wallet/', include('casino_app.wallet.urls')),
    path('lucky_numbers/', include('casino_app.lucky_numbers.urls')),
    path('golitep/', include('casino_app.golitep.urls')),
    path('roulette/', include('casino_app.roulette.urls')),
    path('slots/', include('casino_app.slots.urls')),
    path('blackjack/', include('casino_app.blackjack.urls')),
    path('poker/', include('casino_app.poker.urls')),
    path('baccarat/', include('casino_app.baccarat.urls')),
    path('craps/', include('casino_app.craps.urls')),
    path('keno/', include('casino_app.keno.urls')),
    path('bingo/', include('casino_app.bingo.urls')),
    path('sic_bo/', include('casino_app.sic_bo.urls')),
    path('pai_gow/', include('casino_app.pai_gow.urls')),
    path('fan_tan/', include('casino_app.fan_tan.urls')),
    path('red_dog/', include('casino_app.red_dog.urls')),
    path('three_card_poker/', include('casino_app.three_card_poker.urls')),
    path('caribbean_stud_poker/', include('casino_app.caribbean_stud_poker.urls')),
    path('let_it_ride/', include('casino_app.let_it_ride.urls')),
    path('casino_war/', include('casino_app.casino_war.urls')),
    path('pontoon/', include('casino_app.pontoon.urls')),
    path('spanish_21/', include('casino_app.spanish_21.urls')),
    path('double_exposure_blackjack/', include('casino_app.double_exposure_blackjack.urls')),
    path('omaha_poker/', include('casino_app.omaha_poker.urls')),
    path('texas_holdem/', include('casino_app.texas_holdem.urls')),
    path('video_poker/', include('casino_app.video_poker.urls')),
    path('scratch_cards/', include('casino_app.scratch_cards.urls')),
    path('checkers/', include('casino_app.checkers.urls')),
    path('ludo/', include('casino_app.ludo.urls')),
    path('rock_paper_scissors/', include('casino_app.rock_paper_scissors.urls')),
    path('face_ou_pile/', include('casino_app.face_ou_pile.urls')),

    # JWT token endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Wallet DRF endpoints
    path('api/wallet/', include('casino_app.wallet.api_urls')),
    path('api/lucky_numbers/', include('casino_app.lucky_numbers.api_urls')),
    path('api/golitep/', include('casino_app.golitep.api_urls')),
    path('api/roulette/', include('casino_app.roulette.api_urls')),
    path('api/slots/', include('casino_app.slots.api_urls')),
    path('api/blackjack/', include('casino_app.blackjack.api_urls')),
    path('api/poker/', include('casino_app.poker.api_urls')),
    path('api/baccarat/', include('casino_app.baccarat.api_urls')),
    path('api/craps/', include('casino_app.craps.api_urls')),
    path('api/keno/', include('casino_app.keno.api_urls')),
    path('api/bingo/', include('casino_app.bingo.api_urls')),
    path('api/sic_bo/', include('casino_app.sic_bo.api_urls')),
    path('api/pai_gow/', include('casino_app.pai_gow.api_urls')),
    path('api/fan_tan/', include('casino_app.fan_tan.api_urls')),
    path('api/red_dog/', include('casino_app.red_dog.api_urls')),
    path('api/three_card_poker/', include('casino_app.three_card_poker.api_urls')),
    path('api/caribbean_stud_poker/', include('casino_app.caribbean_stud_poker.api_urls')),
    path('api/let_it_ride/', include('casino_app.let_it_ride.api_urls')),
    path('api/casino_war/', include('casino_app.casino_war.api_urls')),
    path('api/pontoon/', include('casino_app.pontoon.api_urls')),
    path('api/spanish_21/', include('casino_app.spanish_21.api_urls')),
    path('api/double_exposure_blackjack/', include('casino_app.double_exposure_blackjack.api_urls')),
    path('api/omaha_poker/', include('casino_app.omaha_poker.api_urls')),
    path('api/texas_holdem/', include('casino_app.texas_holdem.api_urls')),
    path('api/video_poker/', include('casino_app.video_poker.api_urls')),
    path('api/scratch_cards/', include('casino_app.scratch_cards.api_urls')),
    path('api/rock_paper_scissors/', include('casino_app.rock_paper_scissors.api_urls')),
    path('api/face_ou_pile/', include('casino_app.face_ou_pile.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    
    # Ignorer les requêtes Chrome DevTools pour éviter les erreurs 404 dans les logs
    from django.http import HttpResponse
    from django.urls import re_path
    
    def chrome_devtools_silence(request):
        """Retourne une réponse vide pour les requêtes Chrome DevTools"""
        return HttpResponse('', status=200)
    
    urlpatterns += [
        re_path(r'^\.well-known/appspecific/com\.chrome\.devtools\.json$', chrome_devtools_silence),
    ]

