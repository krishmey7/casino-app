from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('connexion/', views.affichage_connexion, name='connexion'),
    path('inscription/', views.affichage_inscription, name='inscription'),
    path('deconnexion/', views.affichage_deconnexion, name='deconnexion'),
    path('jeux/', views.jeux, name='jeux'),
  
    
]
