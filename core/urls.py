from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('profile/', views.profile_view, name='profile'),

    # Customer
    path('menu/', views.menu_view, name='menu'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('demo/pay/<str:order_number>/', views.demo_pay, name='demo_pay'),
    path('api/payment-status/<str:order_number>/', views.payment_status_api, name='payment_status'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),

    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/menu/', views.admin_menu, name='admin_menu'),
    path('admin-panel/orders/', views.admin_orders, name='admin_orders'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/<int:user_id>/role/', views.update_user_role, name='update_user_role'),
    path('admin-panel/areas/', views.admin_areas, name='admin_areas'),
    path('admin-panel/areas/<int:area_id>/delete/', views.delete_area, name='delete_area'),

    # Kitchen
    path('kitchen/', views.kitchen_dashboard, name='kitchen_dashboard'),
    path('kitchen/order/<int:order_id>/preparing/', views.mark_preparing, name='mark_preparing'),

    # Delivery
    path('delivery/', views.delivery_dashboard, name='delivery_dashboard'),
    path('delivery/order/<int:order_id>/update/', views.update_delivery_status, name='update_delivery_status'),
]
