from django.urls import path
from . import views

urlpatterns = [
    path('', views.wallet_view, name='wallet'),
    path('balance/', views.balance_view, name='wallet_balance'),
    path('credit/', views.credit_view, name='wallet_credit'),
    path('debit/', views.debit_view, name='wallet_debit'),
]
