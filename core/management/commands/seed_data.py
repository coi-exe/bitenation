from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from core.models import User, FoodItem, DeliveryArea


class Command(BaseCommand):
    help = 'Seed initial data for Bite Nation'

    def handle(self, *args, **kwargs):
        # Delivery areas
        areas = [
            ('Gangarithi', 80),
            ('Kandara', 100),
            ('Classic', 60),
            ('Nyeri Town', 50),
        ]
        for name, fee in areas:
            DeliveryArea.objects.get_or_create(name=name, defaults={'delivery_fee': fee})
        self.stdout.write(self.style.SUCCESS('✓ Delivery areas seeded'))

        # Demo users — passwords meet strict rules: upper + lower + number + special
        accounts = [
            ('admin',    'admin@bitenation.com',    '0700000000', 'Admin@123',    'admin',    'Admin',   True,  True),
            ('kitchen',  'kitchen@bitenation.com',  '0711111111', 'Kitchen@123',  'kitchen',  'Kitchen', False, False),
            ('delivery', 'delivery@bitenation.com', '0722222222', 'Delivery@123', 'delivery', 'Rider',   False, False),
        ]
        for username, email, phone, pw, role, fname, is_staff, is_super in accounts:
            if not User.objects.filter(email=email).exists():
                User.objects.create(
                    username=username, email=email, phone=phone,
                    password=make_password(pw), role=role, first_name=fname,
                    is_staff=is_staff, is_superuser=is_super,
                    email_verified=True,
                )
        self.stdout.write(self.style.SUCCESS('✓ Demo users seeded'))

        # Food items
        if FoodItem.objects.count() == 0:
            items = [
                ('Nyama Choma', 'Slow-roasted goat meat, served with kachumbari and ugali.', 850, 'Grills',
                 'https://images.unsplash.com/photo-1558030006-450675393462?w=600&h=400&fit=crop'),
                ('Tilapia Fry', 'Whole fried Nile tilapia with ugali, sukuma wiki and lemon.', 650, 'Fish',
                 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600&h=400&fit=crop'),
                ('Chicken Pilau', 'Aromatic spiced rice slow-cooked with tender chicken pieces.', 450, 'Rice',
                 'https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600&h=400&fit=crop'),
                ('Githeri Special', 'Hearty mix of maize and beans cooked with assorted vegetables.', 200, 'Traditional',
                 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600&h=400&fit=crop'),
                ('Beef Burger', 'Juicy beef patty with cheese, fresh lettuce, tomato & special sauce.', 380, 'Fast Food',
                 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&h=400&fit=crop'),
                ('Ugali & Sukuma', 'Classic Kenyan staple — firm ugali paired with sauteed collard greens.', 150, 'Traditional',
                 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600&h=400&fit=crop'),
                ('Samosa (3 pcs)', 'Crispy pastry filled with spiced minced beef and vegetables.', 120, 'Snacks',
                 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&h=400&fit=crop'),
                ('Passion Juice 500ml', 'Freshly blended passion fruit juice, chilled and served cold.', 100, 'Drinks',
                 'https://images.unsplash.com/photo-1534353436294-0dbd4bdac845?w=600&h=400&fit=crop'),
                ('Beef Stew & Rice', 'Rich slow-cooked beef stew served over fluffy white rice.', 350, 'Rice',
                 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=600&h=400&fit=crop'),
                ('Chips Masala', 'Crispy fries tossed in a spiced tomato masala sauce.', 200, 'Snacks',
                 'https://images.unsplash.com/photo-1548340748-6d2b7d7da280?w=600&h=400&fit=crop'),
            ]
            for name, desc, price, cat, img in items:
                FoodItem.objects.create(name=name, description=desc, price=price, category=cat, image_url=img)
            self.stdout.write(self.style.SUCCESS('✓ Menu items seeded'))

        self.stdout.write(self.style.SUCCESS('\n🍊 Bite Nation ready! http://127.0.0.1:8000'))
        self.stdout.write('   Admin:    admin@bitenation.com    / Admin@123')
        self.stdout.write('   Kitchen:  kitchen@bitenation.com  / Kitchen@123')
        self.stdout.write('   Delivery: delivery@bitenation.com / Delivery@123')
