# Migration neutralisée lors du renommage d'app: conservez l'historique sans appliquer de suppressions automatiques.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('casino_app', '0001_initial'),
    ]

    operations = []
