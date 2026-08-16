from django.urls import path
from . import api_views

urlpatterns = [
    path('balance/', api_views.balance_api, name='wallet_api_balance'),
    path('credit/', api_views.credit_api, name='wallet_api_credit'),
    path('debit/', api_views.debit_api, name='wallet_api_debit'),
]
