from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from .models import LudoGame, LudoPlayer, LudoGameTransaction
from .services import GameService, WalletService
from .rules import LudoRules
from .engine import LudoEngine


class LudoGameModelTest(TestCase):
    """Tests pour le modèle LudoGame"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_game_creation(self):
        """Test la création d'une partie"""
        game = LudoGame.objects.create(stake=Decimal('10.00'))
        game.initialize_game_state()
        
        self.assertEqual(game.status, 'waiting')
        self.assertEqual(game.stake, Decimal('10.00'))
        self.assertIsNotNone(game.game_state)
    
    def test_add_player_to_state(self):
        """Test l'ajout d'un joueur à l'état du jeu"""
        game = LudoGame.objects.create(stake=Decimal('10.00'))
        game.initialize_game_state()
        game.add_player_to_state('red')
        
        self.assertIn('red', game.game_state['players'])
        self.assertEqual(game.game_state['players']['red']['tokens'], [-1, -1, -1, -1])
    
    def test_can_start(self):
        """Test si une partie peut démarrer"""
        game = LudoGame.objects.create(stake=Decimal('10.00'))
        game.initialize_game_state()
        
        # Pas de joueurs, ne peut pas démarrer
        self.assertFalse(game.can_start())
        
        # Ajouter un joueur, ne peut toujours pas démarrer (minimum 2)
        LudoPlayer.objects.create(
            game=game,
            user=self.user,
            color='red',
            turn_order=0,
            is_ready=True
        )
        game.add_player_to_state('red')
        self.assertFalse(game.can_start())
        
        # Ajouter un deuxième joueur prêt
        user2 = User.objects.create_user(username='testuser2', password='testpass')
        LudoPlayer.objects.create(
            game=game,
            user=user2,
            color='blue',
            turn_order=1,
            is_ready=True
        )
        game.add_player_to_state('blue')
        self.assertTrue(game.can_start())


class LudoPlayerModelTest(TestCase):
    """Tests pour le modèle LudoPlayer"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.game = LudoGame.objects.create(stake=Decimal('10.00'))
    
    def test_player_creation(self):
        """Test la création d'un joueur"""
        player = LudoPlayer.objects.create(
            game=self.game,
            user=self.user,
            color='red',
            turn_order=0
        )
        
        self.assertEqual(player.user, self.user)
        self.assertEqual(player.game, self.game)
        self.assertEqual(player.color, 'red')
        self.assertTrue(player.is_connected)
        self.assertFalse(player.is_ready)
    
    def test_mark_ready(self):
        """Test le marquage comme prêt"""
        player = LudoPlayer.objects.create(
            game=self.game,
            user=self.user,
            color='red',
            turn_order=0
        )
        
        self.assertFalse(player.is_ready)
        player.mark_ready()
        self.assertTrue(player.is_ready)


class LudoRulesTest(TestCase):
    """Tests pour les règles LUDO"""
    
    def test_roll_dice(self):
        """Test le lancer de dés"""
        dice = LudoRules.roll_dice()
        
        self.assertEqual(len(dice), 1)
        self.assertTrue(1 <= dice[0] <= 6)
    
    def test_can_enter_game(self):
        """Test si un pion peut entrer en jeu"""
        self.assertTrue(LudoRules.can_enter_game(6))
        self.assertFalse(LudoRules.can_enter_game(5))
    
    def test_check_victory(self):
        """Test la vérification de victoire"""
        # Tous les pions terminés
        self.assertTrue(LudoRules.check_victory([61, 61, 61, 61]))
        
        # Pas tous terminés
        self.assertFalse(LudoRules.check_victory([61, 61, 61, 60]))
        
        # Aucun terminé
        self.assertFalse(LudoRules.check_victory([-1, -1, -1, -1]))
    
    def test_gets_extra_turn(self):
        """Test les tours supplémentaires"""
        self.assertTrue(LudoRules.gets_extra_turn(6))
        self.assertFalse(LudoRules.gets_extra_turn(5))
        self.assertTrue(LudoRules.gets_extra_turn(5, captured=True))


class LudoEngineTest(TestCase):
    """Tests pour le moteur de jeu LUDO"""
    
    def setUp(self):
        self.engine = LudoEngine()
    
    def test_initialization(self):
        """Test l'initialisation du moteur"""
        self.assertIsNotNone(self.engine.game_state)
        self.assertIn('players', self.engine.game_state)
        self.assertIn('dice', self.engine.game_state)
    
    def test_add_player(self):
        """Test l'ajout d'un joueur"""
        self.engine.add_player('red')
        
        self.assertIn('red', self.engine.game_state['players'])
        self.assertEqual(
            self.engine.game_state['players']['red']['tokens'],
            [-1, -1, -1, -1]
        )
    
    def test_roll_dice(self):
        """Test le lancer de dés"""
        dice = self.engine.roll_dice()
        
        self.assertEqual(len(dice), 1)
        self.assertTrue(1 <= dice[0] <= 6)
        self.assertEqual(self.engine.game_state['dice'], dice)


class GameServiceTest(TestCase):
    """Tests pour les services de jeu"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        # Créer un wallet pour l'utilisateur
        from casino_app.wallet.models import Wallet
        Wallet.objects.create(utilisateur=self.user, balance=1000.00)
    
    def test_create_game(self):
        """Test la création d'une partie"""
        game = GameService.create_game(self.user, Decimal('10.00'))
        
        self.assertEqual(game.status, 'waiting')
        self.assertEqual(game.stake, Decimal('10.00'))
        self.assertEqual(game.get_player_count(), 1)
        
        # Vérifier que le wallet a été débité
        from casino_app.wallet.models import Wallet
        wallet = Wallet.objects.get(utilisateur=self.user)
        self.assertEqual(wallet.balance, Decimal('990.00'))
    
    def test_join_game(self):
        """Test le rejoindre d'une partie"""
        game = GameService.create_game(self.user, Decimal('10.00'))
        
        user2 = User.objects.create_user(username='testuser2', password='testpass')
        from casino_app.wallet.models import Wallet
        Wallet.objects.create(utilisateur=user2, balance=1000.00)
        
        player = GameService.join_game(game, user2)
        
        self.assertEqual(player.user, user2)
        self.assertEqual(game.get_player_count(), 2)
        
        # Vérifier que le wallet a été débité
        wallet = Wallet.objects.get(utilisateur=user2)
        self.assertEqual(wallet.balance, Decimal('990.00'))


class WalletServiceTest(TestCase):
    """Tests pour les services wallet"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        from casino_app.wallet.models import Wallet
        Wallet.objects.create(utilisateur=self.user, balance=1000.00)
    
    def test_create_stake_transaction(self):
        """Test la création d'une transaction de mise"""
        game = LudoGame.objects.create(stake=Decimal('10.00'))
        
        transaction = WalletService.create_stake_transaction(game, self.user, Decimal('10.00'))
        
        self.assertEqual(transaction.transaction_type, 'stake')
        self.assertEqual(transaction.amount, Decimal('10.00'))
        
        # Vérifier le wallet
        from casino_app.wallet.models import Wallet
        wallet = Wallet.objects.get(utilisateur=self.user)
        self.assertEqual(wallet.balance, Decimal('990.00'))
    
    def test_refund_stake(self):
        """Test le remboursement d'une mise"""
        game = LudoGame.objects.create(stake=Decimal('10.00'))
        WalletService.create_stake_transaction(game, self.user, Decimal('10.00'))
        
        refund = WalletService.refund_stake(game, self.user)
        
        self.assertEqual(refund.transaction_type, 'refund')
        self.assertEqual(refund.amount, Decimal('10.00'))
        
        # Vérifier le wallet
        from casino_app.wallet.models import Wallet
        wallet = Wallet.objects.get(utilisateur=self.user)
        self.assertEqual(wallet.balance, Decimal('1000.00'))
