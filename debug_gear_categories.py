from rental.models import Gear

# Debugging script to print all gear items and their categories
for gear in Gear.objects.all():
    print(f"{gear.id}: {gear.name} - {gear.category}")