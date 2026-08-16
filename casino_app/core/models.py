from django.db import models
from django.conf import settings
import uuid


class Jeu(models.Model):
    KIBUTU = 'kibutu'
    ROULETTE = 'roulette'
    BLACKJACK = 'blackjack'
    MEMORY = 'memory'
    AVIATOR = 'aviator'

    NOM_CHOICES = [
        (KIBUTU, 'Kibutu - Pile ou Face'),
        (ROULETTE, 'Roulette'),
        (BLACKJACK, 'Blackjack'),
        (MEMORY, 'Memory'),
        (AVIATOR, 'Aviator'),
    ]

    nom = models.CharField(max_length=50, choices=NOM_CHOICES, unique=True)
    nom_affichage = models.CharField(max_length=100)
    description = models.TextField()
    mise_min = models.DecimalField(max_digits=10, decimal_places=2, default=500.0)
    mise_max = models.DecimalField(max_digits=10, decimal_places=2, default=100000.0)
    type_jeu = models.CharField(max_length=10, choices=[('solo', 'Solo'), ('multi', 'Multijoueur')])
    commission = models.IntegerField(default=20)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Jeu'
        verbose_name_plural = 'Jeux'

    def __str__(self):
        return self.nom_affichage


class PartieKibutu(models.Model):
    MODE_CHOICES = [('solo', 'Solo'), ('multi', 'Multijoueur')]
    CHOIX_CHOICES = [('pile', 'Pile'), ('face', 'Face')]
    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]

    id_partie = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    mise = models.DecimalField(max_digits=10, decimal_places=2)
    choix_j1 = models.CharField(max_length=10, choices=CHOIX_CHOICES, blank=True)
    choix_j2 = models.CharField(max_length=10, choices=CHOIX_CHOICES, blank=True)
    manche1_resultat = models.CharField(max_length=10, choices=CHOIX_CHOICES, blank=True)
    manche2_resultat = models.CharField(max_length=10, choices=CHOIX_CHOICES, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    commission_totale = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    gains_gagnant = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(blank=True, null=True)

    gagnant_final = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='parties_kibutu_gagnees')
    manche1_gagnant = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='manches_gagnees_1')
    manche2_gagnant = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='manches_gagnees_2')
    utilisateur1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parties_kibutu_j1')
    utilisateur2 = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='parties_kibutu_j2')

    class Meta:
        verbose_name = 'Partie Kibutu'
        verbose_name_plural = 'Parties Kibutu'


class TransactionSolde(models.Model):
    TYPE_CHOICES = [
        ('depot', 'Dépôt'),
        ('retrait', 'Retrait'),
        ('mise', 'Mise'),
        ('gain', 'Gain'),
        ('commission', 'Commission'),
    ]

    type_transaction = models.CharField(max_length=20, choices=TYPE_CHOICES)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    solde_avant = models.DecimalField(max_digits=10, decimal_places=2)
    solde_apres = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date_transaction = models.DateTimeField(auto_now_add=True)

    partie = models.ForeignKey(PartieKibutu, null=True, blank=True, on_delete=models.SET_NULL)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')

    class Meta:
        verbose_name = 'Transaction Solde'
        verbose_name_plural = 'Transactions Solde'
        ordering = ['-date_transaction']


class ProfilUtilisateur(models.Model):
    solde = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    points_vip = models.IntegerField(default=0)
    parties_jouees = models.IntegerField(default=0)
    parties_gagnees = models.IntegerField(default=0)
    total_mise = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    total_gains = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    date_creation = models.DateTimeField(auto_now_add=True)
    dernier_acces = models.DateTimeField(auto_now=True)
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profil')

    class Meta:
        verbose_name = 'Profil Utilisateur'
        verbose_name_plural = 'Profils Utilisateurs'