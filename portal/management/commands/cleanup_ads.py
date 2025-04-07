from django.core.management.base import BaseCommand
from portal.models import Ad
from django.utils import timezone

class Command(BaseCommand):
    help = 'Usuwa ogłoszenia, które wygasły'

    def handle(self, *args, **kwargs):
        expired_ads = Ad.objects.filter(expires_at__lt=timezone.now())
        count = expired_ads.count()
        expired_ads.delete()
        self.stdout.write(self.style.SUCCESS(f'Usunięto {count} wygasłych ogłoszeń.'))