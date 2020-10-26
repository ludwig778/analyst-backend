from django.core.management.base import BaseCommand

from analyst.scrapper import scrap_values


class Command(BaseCommand):
    help = 'Scrap data to populate db with the right dataframes'

    def handle(self, *args, **options):
        scrap_values()
