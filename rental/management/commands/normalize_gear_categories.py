from django.core.management.base import BaseCommand
from rental.models import Gear

class Command(BaseCommand):
    help = 'Normalize gear category values to match choices.'

    def handle(self, *args, **options):
        valid_categories = [c[0] for c in Gear.CATEGORY_CHOICES]
        for gear in Gear.objects.all():
            original = gear.category
            normalized = original.strip().lower().replace(' ', '_')
            if normalized in valid_categories and gear.category != normalized:
                gear.category = normalized
                gear.save()
                self.stdout.write(self.style.SUCCESS(f'Updated {gear.name}: {original} -> {normalized}'))
            elif normalized not in valid_categories:
                self.stdout.write(self.style.WARNING(f'{gear.name}: Invalid category "{original}"'))
        self.stdout.write(self.style.SUCCESS('Category normalization complete.'))
