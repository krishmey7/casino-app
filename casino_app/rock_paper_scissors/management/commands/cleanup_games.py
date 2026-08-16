from django.core.management.base import BaseCommand
from casino_app.rock_paper_scissors.models import RockPaperScissorsGame

class Command(BaseCommand):
    help = 'Clean up old finished games'

    def handle(self, *args, **options):
        # Example: delete games older than 30 days
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=30)
        old_games = RockPaperScissorsGame.objects.filter(status='finished', finished_at__lt=cutoff)
        count = old_games.delete()[0]
        self.stdout.write(f'Deleted {count} old games')