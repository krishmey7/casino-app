from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from decimal import Decimal
from casino_app.wallet.models import Wallet
from .models import FaceOuPileGame

User = get_user_model()


class FaceOuPileGameTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='player1', password='pass123')
        self.user2 = User.objects.create_user(username='player2', password='pass123')
        self.wallet1, _ = Wallet.objects.get_or_create(utilisateur=self.user1)
        self.wallet2, _ = Wallet.objects.get_or_create(utilisateur=self.user2)
        self.wallet1.balance = Decimal('100.00')
        self.wallet1.save()
        self.wallet2.balance = Decimal('100.00')
        self.wallet2.save()
        self.client = APIClient()
        self.client.login(username='player1', password='pass123')

    def test_create_game(self):
        response = self.client.post('/api/face_ou_pile/games/create_game/', {'bet_amount': '10.00'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FaceOuPileGame.objects.count(), 1)
        self.assertEqual(Wallet.objects.get(utilisateur=self.user1).balance, Decimal('90.00'))

    def test_join_and_play_game(self):
        response = self.client.post('/api/face_ou_pile/games/create_game/', {'bet_amount': '10.00'}, format='json')
        game_id = response.data['id']
        self.client.logout()
        self.client.login(username='player2', password='pass123')
        response = self.client.post(f'/api/face_ou_pile/games/{game_id}/join_game/', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Wallet.objects.get(utilisateur=self.user2).balance, Decimal('90.00'))
        self.client.logout()
        self.client.login(username='player1', password='pass123')
        response = self.client.post(f'/api/face_ou_pile/games/{game_id}/make_choice/', {'choice': 'face'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        self.client.login(username='player2', password='pass123')
        response = self.client.post(f'/api/face_ou_pile/games/{game_id}/make_choice/', {'choice': 'pile'}, format='json')
        self.assertEqual(response.status_code, 200)
        game = FaceOuPileGame.objects.get(pk=game_id)
        self.assertEqual(game.status, 'finished')
        self.assertEqual(game.winner, self.user2)

    def test_draw_refunds(self):
        response = self.client.post('/api/face_ou_pile/games/create_game/', {'bet_amount': '10.00'}, format='json')
        game_id = response.data['id']
        self.client.logout()
        self.client.login(username='player2', password='pass123')
        self.client.post(f'/api/face_ou_pile/games/{game_id}/join_game/', format='json')
        self.client.logout()
        self.client.login(username='player1', password='pass123')
        self.client.post(f'/api/face_ou_pile/games/{game_id}/make_choice/', {'choice': 'face'}, format='json')
        self.client.logout()
        self.client.login(username='player2', password='pass123')
        self.client.post(f'/api/face_ou_pile/games/{game_id}/make_choice/', {'choice': 'face'}, format='json')
        self.assertEqual(Wallet.objects.get(utilisateur=self.user1).balance, Decimal('100.00'))
        self.assertEqual(Wallet.objects.get(utilisateur=self.user2).balance, Decimal('100.00'))
