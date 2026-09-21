from django.core.management.base import BaseCommand

from listings.models import Category, CategoryAttribute

# Top-level category -> its subcategories. A top-level entry with an
# empty list has no children, which makes it a leaf itself (is_leaf
# checks for the absence of children) — so it's directly listable.
CATEGORY_TREE = {
    "Consoles": [],
    "PC Components": [
        "Graphics Cards",
        "Processors",
        "RAM",
        "Motherboards",
        "Power Supplies",
        "Storage",
    ],
    "Peripherals": ["Keyboards", "Mice", "Headsets", "Controllers"],
    "Monitors": [],
    "Games & Discs": [
        "PS5 Discs",
        "PS4 Discs",
        "Xbox Discs",
        "Nintendo Switch Cartridges",
    ],
    "Accessories & Merch": [],
}

# Leaf category name -> [(attribute name, data_type, choices, is_required), ...]
# A starting example of category-specific specs — add more of your own
# through /admin/ (Category admin has a CategoryAttribute inline) once
# you see how this pattern works.
ATTRIBUTES = {
    "Graphics Cards": [
        ("VRAM (GB)", CategoryAttribute.NUMBER, None, True),
        ("Wattage", CategoryAttribute.NUMBER, None, False),
    ],
    "Keyboards": [
        (
            "Switch Type",
            CategoryAttribute.CHOICE,
            ["Cherry MX Red", "Cherry MX Blue", "Cherry MX Brown", "Membrane"],
            True,
        ),
    ],
}


class Command(BaseCommand):
    help = "Seed a starter category tree so the listing form's category dropdown isn't empty."

    def handle(self, *args, **options):
        created_count = 0

        for parent_name, children in CATEGORY_TREE.items():
            parent, was_created = Category.objects.get_or_create(name=parent_name)
            created_count += was_created

            for child_name in children:
                child, was_created = Category.objects.get_or_create(
                    name=child_name, parent=parent
                )
                created_count += was_created

                for attr_name, data_type, choices, required in ATTRIBUTES.get(
                    child_name, []
                ):
                    _, attr_created = CategoryAttribute.objects.get_or_create(
                        category=child,
                        name=attr_name,
                        defaults={
                            "data_type": data_type,
                            "choices": choices,
                            "is_required": required,
                        },
                    )
                    created_count += attr_created

        self.stdout.write(
            self.style.SUCCESS(f"Seeded categories — {created_count} new rows created.")
        )