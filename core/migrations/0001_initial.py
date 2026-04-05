from django.db import migrations, models
import django.db.models.deletion
import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False)),
                ('username', models.CharField(
                    error_messages={'unique': 'A user with that username already exists.'},
                    max_length=150,
                    unique=True,
                    validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                    verbose_name='username',
                )),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('phone', models.CharField(default='', max_length=20)),
                ('address', models.TextField(default='')),
                ('role', models.CharField(
                    choices=[
                        ('customer', 'Customer'),
                        ('kitchen', 'Kitchen Admin'),
                        ('delivery', 'Delivery Admin'),
                        ('admin', 'Admin'),
                    ],
                    default='customer',
                    max_length=20,
                )),
                ('groups', models.ManyToManyField(
                    blank=True,
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.group',
                    verbose_name='groups',
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True,
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.permission',
                    verbose_name='user permissions',
                )),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='DeliveryArea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('delivery_fee', models.DecimalField(decimal_places=2, default=100, max_digits=8)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='FoodItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('category', models.CharField(max_length=100)),
                ('image_url', models.URLField(blank=True, default='')),
                ('status', models.CharField(
                    choices=[('available', 'Available'), ('limited', 'Limited'), ('sold_out', 'Sold Out')],
                    default='available',
                    max_length=20,
                )),
                ('stock_note', models.CharField(blank=True, default='', max_length=200)),
                ('discount_percent', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['category', 'name']},
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(max_length=50, unique=True)),
                ('delivery_address', models.TextField()),
                ('delivery_phone', models.CharField(max_length=20)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=10)),
                ('delivery_fee', models.DecimalField(decimal_places=2, default=100, max_digits=8)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_status', models.CharField(
                    choices=[('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed')],
                    default='pending',
                    max_length=20,
                )),
                ('delivery_status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('preparing', 'Preparing'),
                        ('on_the_way', 'On the Way'),
                        ('delivered', 'Delivered'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('mpesa_checkout_id', models.CharField(blank=True, default='', max_length=200)),
                ('mpesa_receipt', models.CharField(blank=True, default='', max_length=100)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='core.user')),
                ('delivery_area', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='core.deliveryarea',
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('food_name', models.CharField(max_length=200)),
                ('quantity', models.PositiveIntegerField()),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.order')),
                ('food_item', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='core.fooditem',
                )),
            ],
        ),
    ]
