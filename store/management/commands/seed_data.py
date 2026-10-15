from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Category, Product


class Command(BaseCommand):
    help = 'Seed the database with categories, products, and a superuser'

    def handle(self, *args, **options):
        # Create superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Superuser created: admin / admin123'))
        else:
            self.stdout.write('Superuser already exists')

        # Create categories
        categories_data = ['Apparel', 'Accessories', 'Home Goods']
        for name in categories_data:
            Category.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS(f'Categories: {Category.objects.count()}'))

        # Create products
        products_data = {
            'Apparel': [
                ('T-Shirt', 'Cotton tee, sizes S/M/L', 4900),
                ('Oversized Tee', 'Heavy cotton 240gsm, oversized fit', 5900),
                ('Hoodie', 'Fleece-lined, drawstring hood', 9900),
                ('Cargo Pants', 'Multiple pockets, tapered fit', 7900),
            ],
            'Accessories': [
                ('Cap', 'Six-panel, adjustable strap', 3500),
                ('Tote Bag', 'Canvas, heavy duty', 2900),
                ('Beanie', 'Ribbed knit, one size', 2500),
            ],
            'Home Goods': [
                ('Coffee Mug', 'Ceramic 350ml mug', 2500),
                ('Notebook', 'A5 dotted grid, 200 pages', 1500),
                ('Poster', 'A2 matte print, framed', 4500),
            ],
        }

        for cat_name, products in products_data.items():
            cat = Category.objects.get(name=cat_name)
            for name, desc, price in products:
                Product.objects.get_or_create(
                    name=name,
                    defaults={'description': desc, 'price': price, 'category': cat}
                )

        self.stdout.write(self.style.SUCCESS(f'Products: {Product.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('Seed complete!'))
