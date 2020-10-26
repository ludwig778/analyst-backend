from django.core.management.base import BaseCommand

from analyst.scrapper import scrap_investing


class Command(BaseCommand):
    help = 'Scrap init'

    def add_arguments(self, parser):
        parser.add_argument('--show-indices', action='store_true')

    def handle(self, *args, **options):
        scrap_investing(**options)
