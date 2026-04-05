from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, FoodItem, Order, OrderItem, DeliveryArea


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'phone', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'phone')
    ordering = ('-date_joined',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Bite Nation', {'fields': ('phone', 'address', 'role')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Bite Nation', {'fields': ('phone', 'address', 'role')}),
    )


@admin.register(DeliveryArea)
class DeliveryAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'delivery_fee', 'is_active')
    list_editable = ('delivery_fee', 'is_active')
    ordering = ('name',)


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount_percent', 'status', 'is_active')
    list_filter = ('category', 'status', 'is_active')
    list_editable = ('price', 'status', 'is_active')
    search_fields = ('name', 'category')
    ordering = ('category', 'name')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('food_name', 'quantity', 'unit_price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'delivery_area', 'total', 'payment_status', 'delivery_status', 'created_at')
    list_filter = ('payment_status', 'delivery_status', 'delivery_area')
    search_fields = ('order_number', 'user__email', 'user__first_name', 'delivery_phone')
    ordering = ('-created_at',)
    readonly_fields = ('order_number', 'created_at', 'delivered_at', 'mpesa_receipt', 'mpesa_checkout_id')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Info', {'fields': ('order_number', 'user', 'created_at')}),
        ('Delivery', {'fields': ('delivery_area', 'delivery_address', 'delivery_phone', 'notes')}),
        ('Amounts', {'fields': ('subtotal', 'delivery_fee', 'total')}),
        ('Status', {'fields': ('payment_status', 'delivery_status', 'delivered_at')}),
        ('M-Pesa', {'fields': ('mpesa_checkout_id', 'mpesa_receipt')}),
    )
