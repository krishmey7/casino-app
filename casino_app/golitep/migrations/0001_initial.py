# Generated migration for Mines models

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
            name='MinesGame',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('waiting', 'En attente'), ('playing', 'En cours'), ('won', 'Gagné'), ('lost', 'Perdu')], default='playing', max_length=10)),
                ('difficulty', models.CharField(choices=[('easy', 'Facile (1 mine)'), ('medium', 'Moyen (12 mines)'), ('hard', 'Difficile (24 mines)'), ('custom', 'Personnalisé')], default='medium', max_length=10)),
                ('grid', models.JSONField(default=list)),
                ('revealed', models.JSONField(default=list)),
                ('bet_amount', models.DecimalField(decimal_places=2, default='100.00', max_digits=12)),
                ('current_multiplier', models.DecimalField(decimal_places=2, default='1.00', max_digits=10)),
                ('winnings', models.DecimalField(blank=True, decimal_places=2, default='0.00', max_digits=12, null=True)),
                ('cells_revealed', models.IntegerField(default=0)),
                ('mines_count', models.IntegerField(default=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mines_games', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
