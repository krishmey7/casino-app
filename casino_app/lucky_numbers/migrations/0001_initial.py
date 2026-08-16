# Generated migration for LuckyNumbers models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LuckyNumberGame',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('waiting', 'En attente'), ('playing', 'En cours'), ('finished', 'Fini')], default='waiting', max_length=10)),
                ('winning_number', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='LuckyNumberBet',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('chosen_number', models.IntegerField()),
                ('bet_amount', models.DecimalField(decimal_places=2, default='100.00', max_digits=12)),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('won', 'Gagné'), ('lost', 'Perdu')], default='pending', max_length=10)),
                ('winnings', models.DecimalField(blank=True, decimal_places=2, default='0.00', max_digits=12, null=True)),
                ('bet_time', models.DateTimeField(auto_now_add=True)),
                ('result_time', models.DateTimeField(blank=True, null=True)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bets', to='lucky_numbers.luckynumbergame')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lucky_number_bets', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
