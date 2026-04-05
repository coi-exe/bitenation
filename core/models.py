from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('kitchen', 'Kitchen Admin'),
        ('delivery', 'Delivery Admin'),
        ('admin', 'Admin'),
    ]
    phone = models.CharField(max_length=20, default='')
    address = models.TextField(default='')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=64, default='', blank=True)
    # Login OTP
    otp_code = models.CharField(max_length=6, default='', blank=True)
    otp_expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class DeliveryArea(models.Model):
    name = models.CharField(max_length=100, unique=True)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (KSh {self.delivery_fee})"

    class Meta:
        ordering = ['name']


class FoodItem(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('limited', 'Limited'),
        ('sold_out', 'Sold Out'),
    ]
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    image_url = models.URLField(default='', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    stock_note = models.CharField(max_length=200, default='', blank=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def discounted_price(self):
        if self.discount_percent and self.discount_percent > 0:
            return round(float(self.price) * (1 - float(self.discount_percent) / 100), 2)
        return float(self.price)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['category', 'name']


class Order(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    DELIVERY_STATUS = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('on_the_way', 'On the Way'),
        ('delivered', 'Delivered'),
    ]
    order_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    delivery_area = models.ForeignKey(DeliveryArea, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_address = models.TextField()
    delivery_phone = models.CharField(max_length=20)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=100)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='pending')
    mpesa_checkout_id = models.CharField(max_length=200, default='', blank=True)
    mpesa_receipt = models.CharField(max_length=100, default='', blank=True)
    notes = models.TextField(default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.order_number

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.SET_NULL, null=True)
    food_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def line_total(self):
        return float(self.unit_price) * self.quantity

    def __str__(self):
        return f"{self.food_name} x{self.quantity}"
