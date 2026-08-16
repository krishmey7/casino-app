from django.urls import path
from . import views

app_name = 'checkers'

urlpatterns = [
    path('lobby/', views.lobby, name='lobby'),
    path('create/', views.create_game, name='create_game'),
    path('waiting/<uuid:game_id>/', views.waiting_room, name='waiting_room'),
    path('join/<uuid:game_id>/', views.join_game, name='join_game'),
    path('game/<uuid:game_id>/', views.game_view, name='game'),
    path('cancel/<uuid:game_id>/', views.cancel_game, name='cancel_game'),
    path('api/state/<uuid:game_id>/', views.api_game_state, name='api_game_state'),
    path('move/<uuid:game_id>/', views.make_move, name='make_move'),
    path('forfeit/<uuid:game_id>/', views.forfeit_game, name='forfeit_game'),
    path('test/', views.game_test, name='game_test'),
]
