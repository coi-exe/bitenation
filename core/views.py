from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from functools import wraps
from datetime import timedelta
import json, uuid, re, base64, random, string
import requests as http_requests
from datetime import datetime

from .models import User, FoodItem, Order, OrderItem, DeliveryArea


# ── HELPERS ──────────────────────────────────────────────────────────────────

def validate_password(pw):
    errors = []
    if len(pw) < 8:
        errors.append('Password must be at least 8 characters.')
    if not re.search(r'[A-Z]', pw):
        errors.append('Password must contain at least one uppercase letter.')
    if not re.search(r'[a-z]', pw):
        errors.append('Password must contain at least one lowercase letter.')
    if not re.search(r'\d', pw):
        errors.append('Password must contain at least one number.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-]', pw):
        errors.append('Password must contain at least one special character (!@#$...)')
    return errors

def validate_phone(phone):
    cleaned = re.sub(r'[\s\-]', '', phone)
    return bool(re.match(r'^(07|01|2547|2541)\d{8}$', cleaned))

def send_verification_email(user, request):
    token = uuid.uuid4().hex
    user.email_token = token
    user.email_verified = False
    user.save(update_fields=['email_token', 'email_verified'])
    scheme = 'https' if request.is_secure() else 'http'
    link = f"{scheme}://{request.get_host()}/verify-email/{token}/"
    try:
        send_mail(
            subject='Verify your Bite Nation account',
            message=f"Hi {user.first_name or user.username},\n\n"
                    f"Welcome to Bite Nation! 🍊\n\n"
                    f"Click to verify your email:\n{link}\n\n"
                    f"If you didn't register, ignore this.\n\n– Bite Nation",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False

def send_otp_email(user):
    code = ''.join(random.choices(string.digits, k=6))
    user.otp_code = code
    user.otp_expires = timezone.now() + timedelta(minutes=10)
    user.save(update_fields=['otp_code', 'otp_expires'])
    try:
        send_mail(
            subject='Your Bite Nation login code',
            message=f"Hi {user.first_name or user.username},\n\n"
                    f"Your login verification code is:\n\n"
                    f"  {code}\n\n"
                    f"This code expires in 10 minutes.\n"
                    f"If you didn't request this, someone may have your password — change it immediately.\n\n"
                    f"– Bite Nation",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception:
        return False


# ── DECORATORS ───────────────────────────────────────────────────────────────

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please log in to continue.')
                return redirect('login')
            if request.user.is_superuser or request.user.role in roles:
                return f(request, *args, **kwargs)
            messages.error(request, 'Access denied.')
            return redirect('index')
        return wrapped
    return decorator

admin_required    = role_required('admin')
kitchen_required  = role_required('admin', 'kitchen')
delivery_required = role_required('admin', 'delivery')


# ── AUTH ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return _role_redirect(request.user)

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'core/login.html')

        user = authenticate(request, username=user_obj.username, password=password)
        if not user:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'core/login.html')

        # Email verification check (skip for superusers)
        if not user.is_superuser and not user.email_verified:
            messages.warning(request, 'Please verify your email before logging in.')
            return render(request, 'core/login.html', {'unverified_email': email})

        # OTP — skip for superusers, try to send
        if not user.is_superuser:
            sent = send_otp_email(user)
            if sent:
                # Store pending user id in session (not logged in yet)
                request.session['otp_user_id'] = user.id
                return redirect('verify_otp')
            else:
                # SMTP not configured — skip OTP, log straight in (dev mode)
                login(request, user)
                return _role_redirect(user)

        login(request, user)
        return _role_redirect(user)

    return render(request, 'core/login.html')


def verify_otp_view(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        entered = request.POST.get('otp', '').strip()

        if not user.otp_code or not user.otp_expires:
            messages.error(request, 'No OTP found. Please log in again.')
            return redirect('login')

        if timezone.now() > user.otp_expires:
            messages.error(request, 'Code expired. Please log in again.')
            return redirect('login')

        if entered != user.otp_code:
            messages.error(request, 'Incorrect code. Try again.')
            return render(request, 'core/verify_otp.html', {'email': user.email})

        # Clear OTP
        user.otp_code = ''
        user.otp_expires = None
        user.save(update_fields=['otp_code', 'otp_expires'])

        del request.session['otp_user_id']
        login(request, user)
        return _role_redirect(user)

    return render(request, 'core/verify_otp.html', {'email': user.email})


def resend_otp(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('login')
    try:
        user = User.objects.get(id=user_id)
        send_otp_email(user)
        messages.success(request, 'A new code has been sent to your email.')
    except User.DoesNotExist:
        pass
    return redirect('verify_otp')


def _role_redirect(user):
    if user.is_superuser or user.role == 'admin':
        return redirect('admin_dashboard')
    if user.role == 'kitchen':
        return redirect('kitchen_dashboard')
    if user.role == 'delivery':
        return redirect('delivery_dashboard')
    return redirect('index')


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        name     = request.POST.get('name', '').strip()
        email    = request.POST.get('email', '').strip().lower()
        phone    = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm  = request.POST.get('confirm_password', '')
        ctx      = {'name': name, 'email': email, 'phone': phone}

        if not all([name, email, phone, password, confirm]):
            messages.error(request, 'All fields are required.')
            return render(request, 'core/register.html', ctx)
        if not re.match(r'^[a-zA-Z\s]{2,50}$', name):
            messages.error(request, 'Name must be 2–50 letters only.')
            return render(request, 'core/register.html', ctx)
        if not re.match(r'^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$', email):
            messages.error(request, 'Enter a valid email address.')
            return render(request, 'core/register.html', ctx)
        if not validate_phone(phone):
            messages.error(request, 'Enter a valid Kenyan phone number (07XX or 01XX).')
            return render(request, 'core/register.html', ctx)
        for err in validate_password(password):
            messages.error(request, err)
        if any(True for _ in validate_password(password)):
            return render(request, 'core/register.html', ctx)
        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'core/register.html', ctx)
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'core/register.html', ctx)

        username = email.split('@')[0] + '_' + uuid.uuid4().hex[:4]
        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=name, phone=phone,
        )
        sent = send_verification_email(user, request)
        if sent:
            messages.success(request,
                f'Account created! A verification link has been sent to {email}. '
                'Check your inbox (and spam folder) before logging in.')
        else:
            # SMTP not configured — auto-verify for dev
            user.email_verified = True
            user.save(update_fields=['email_verified'])
            messages.success(request,
                'Account created! (Email sending not configured — auto-verified for dev.) You can now log in.')
        return redirect('login')
    return render(request, 'core/register.html')


def verify_email(request, token):
    try:
        user = User.objects.get(email_token=token)
        user.email_verified = True
        user.email_token = ''
        user.save(update_fields=['email_verified', 'email_token'])
        messages.success(request, '✅ Email verified! You can now log in.')
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')
    return redirect('login')


def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            user = User.objects.get(email=email, email_verified=False)
            send_verification_email(user, request)
            messages.success(request, f'Verification email resent to {email}.')
        except User.DoesNotExist:
            messages.error(request, 'No unverified account with that email.')
    return redirect('login')


# ── CUSTOMER ─────────────────────────────────────────────────────────────────

def index(request):
    featured   = FoodItem.objects.filter(is_active=True)[:3]
    categories = FoodItem.objects.filter(is_active=True).values_list('category', flat=True).distinct()
    return render(request, 'core/index.html', {'featured': featured, 'categories': categories})


def menu_view(request):
    cat = request.GET.get('category', 'all')
    qs  = FoodItem.objects.filter(is_active=True)
    if cat != 'all':
        qs = qs.filter(category=cat)
    categories = FoodItem.objects.filter(is_active=True).values_list('category', flat=True).distinct()
    return render(request, 'core/menu.html', {'items': qs, 'categories': categories, 'active_category': cat})


@login_required
def cart_view(request):
    areas = DeliveryArea.objects.filter(is_active=True)
    return render(request, 'core/cart.html', {'areas': areas})


@login_required
def checkout_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid data'})

        cart_items = data.get('cart', [])
        address    = data.get('address', '').strip()
        phone      = data.get('phone', '').strip()
        notes      = data.get('notes', '')
        area_id    = data.get('area_id')

        if not cart_items:
            return JsonResponse({'success': False, 'message': 'Cart is empty'})
        if not address or not phone:
            return JsonResponse({'success': False, 'message': 'Address and phone required'})

        area = None
        delivery_fee = 100
        if area_id:
            try:
                area = DeliveryArea.objects.get(id=area_id, is_active=True)
                delivery_fee = float(area.delivery_fee)
            except DeliveryArea.DoesNotExist:
                pass

        subtotal  = 0
        validated = []
        for ci in cart_items:
            try:
                food = FoodItem.objects.get(id=ci['id'])
            except FoodItem.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'An item is unavailable'})
            if food.status == 'sold_out':
                return JsonResponse({'success': False, 'message': f'{food.name} is sold out'})
            price     = food.discounted_price
            subtotal += price * ci['qty']
            validated.append({'food': food, 'qty': ci['qty'], 'price': price})

        total     = subtotal + delivery_fee
        order_num = f"BN{timezone.now().strftime('%Y%m%d%H%M%S')}"
        order = Order.objects.create(
            order_number=order_num, user=request.user,
            delivery_area=area, delivery_address=address,
            delivery_phone=phone, subtotal=subtotal,
            delivery_fee=delivery_fee, total=total, notes=notes,
        )
        for v in validated:
            OrderItem.objects.create(
                order=order, food_item=v['food'],
                food_name=v['food'].name, quantity=v['qty'], unit_price=v['price'],
            )

        # Try real STK push if keys are configured
        if settings.MPESA_CONSUMER_KEY != 'YOUR_CONSUMER_KEY':
            try:
                result      = stk_push(phone, total, order_num)
                checkout_id = result.get('CheckoutRequestID', '')
                order.mpesa_checkout_id = checkout_id
                order.save(update_fields=['mpesa_checkout_id'])
                return JsonResponse({
                    'success': True, 'order_id': order.id,
                    'order_number': order_num,
                    'checkout_request_id': checkout_id,
                    'message': 'STK Push sent',
                })
            except Exception:
                pass

        return JsonResponse({
            'success': True, 'order_id': order.id,
            'order_number': order_num,
            'checkout_request_id': f'DEMO_{order_num}',
            'message': 'Order placed (Demo mode)',
        })

    areas = DeliveryArea.objects.filter(is_active=True)
    return render(request, 'core/checkout.html', {'user': request.user, 'areas': areas})


# ── M-PESA ───────────────────────────────────────────────────────────────────

def _mpesa_token():
    creds = base64.b64encode(
        f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()
    ).decode()
    r = http_requests.get(
        f"{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
        headers={"Authorization": f"Basic {creds}"}, timeout=10,
    )
    return r.json().get('access_token')


def stk_push(phone, amount, order_number):
    token = _mpesa_token()
    ts    = datetime.now().strftime('%Y%m%d%H%M%S')
    pw    = base64.b64encode(
        f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{ts}".encode()
    ).decode()
    phone = re.sub(r'[\s\-]', '', phone)
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('+'):
        phone = phone[1:]
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": pw, "Timestamp": ts,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone, "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": order_number,
        "TransactionDesc": f"Order {order_number}",
    }
    r = http_requests.post(
        f"{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=15,
    )
    return r.json()


@csrf_exempt
def mpesa_callback(request):
    try:
        body        = json.loads(request.body)
        stk         = body.get('Body', {}).get('stkCallback', {})
        result_code = stk.get('ResultCode')
        checkout_id = stk.get('CheckoutRequestID', '')
        if result_code == 0:
            items   = stk.get('CallbackMetadata', {}).get('Item', [])
            receipt = next((i['Value'] for i in items if i['Name'] == 'MpesaReceiptNumber'), '')
            Order.objects.filter(mpesa_checkout_id=checkout_id).update(
                payment_status='paid', mpesa_receipt=receipt,
            )
        else:
            Order.objects.filter(mpesa_checkout_id=checkout_id).update(payment_status='failed')
    except Exception:
        pass
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})


@login_required
def payment_status_api(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number, user=request.user)
        return JsonResponse({
            'payment_status': order.payment_status,
            'delivery_status': order.delivery_status,
            'mpesa_receipt':   order.mpesa_receipt,
        })
    except Order.DoesNotExist:
        return JsonResponse({'status': 'not_found'})


@login_required
def demo_pay(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    order.payment_status = 'paid'
    order.mpesa_receipt  = 'DEMO' + order_number[-6:]
    order.save()
    messages.success(request, '✅ Payment confirmed! (Demo mode)')
    return redirect('order_detail', order_id=order.id)


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'core/orders.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'core/order_detail.html', {'order': order, 'items': order.items.all()})


@login_required
def profile_view(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        phone   = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        new_pw  = request.POST.get('new_password', '')
        cur_pw  = request.POST.get('current_password', '')

        if not re.match(r'^[a-zA-Z\s]{2,50}$', name):
            messages.error(request, 'Name must be 2–50 letters only.')
            return render(request, 'core/profile.html')
        if not validate_phone(phone):
            messages.error(request, 'Enter a valid Kenyan phone number.')
            return render(request, 'core/profile.html')

        request.user.first_name = name
        request.user.phone      = phone
        request.user.address    = address

        if new_pw:
            if not request.user.check_password(cur_pw):
                messages.error(request, 'Current password is incorrect.')
                return render(request, 'core/profile.html')
            for err in validate_password(new_pw):
                messages.error(request, err)
            if validate_password(new_pw):
                return render(request, 'core/profile.html')
            request.user.set_password(new_pw)
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully.')

        request.user.save()
        messages.success(request, 'Profile updated!')
        return redirect('profile')
    return render(request, 'core/profile.html')


# ── ADMIN ─────────────────────────────────────────────────────────────────────

@admin_required
def admin_dashboard(request):
    from django.db.models import Sum
    total_orders  = Order.objects.count()
    paid_orders   = Order.objects.filter(payment_status='paid').count()
    preparing     = Order.objects.filter(delivery_status='preparing').count()
    on_way        = Order.objects.filter(delivery_status='on_the_way').count()
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(s=Sum('total'))['s'] or 0
    recent_orders = Order.objects.select_related('user', 'delivery_area').order_by('-created_at')[:10]
    return render(request, 'admin_panel/dashboard.html', {
        'total_orders': total_orders, 'paid_orders': paid_orders,
        'preparing': preparing, 'on_way': on_way,
        'total_revenue': total_revenue, 'recent_orders': recent_orders,
    })


@admin_required
def admin_menu(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            FoodItem.objects.create(
                name=request.POST['name'],
                description=request.POST['description'],
                price=float(request.POST['price']),
                category=request.POST['category'],
                image_url=request.POST.get('image_url', ''),
                status=request.POST.get('status', 'available'),
                stock_note=request.POST.get('stock_note', ''),
                discount_percent=float(request.POST.get('discount_percent', 0)),
            )
            messages.success(request, 'Food item added!')
        elif action == 'update':
            item = get_object_or_404(FoodItem, id=request.POST['item_id'])
            item.price            = float(request.POST.get('price', item.price))
            item.discount_percent = float(request.POST.get('discount_percent', 0))
            item.status           = request.POST.get('status', item.status)
            item.stock_note       = request.POST.get('stock_note', '')
            item.is_active        = request.POST.get('is_active') == '1'
            item.save()
            messages.success(request, 'Item updated!')
        elif action == 'delete':
            get_object_or_404(FoodItem, id=request.POST['item_id']).delete()
            messages.success(request, 'Item deleted.')
        return redirect('admin_menu')
    return render(request, 'admin_panel/menu.html', {'items': FoodItem.objects.all()})


@admin_required
def admin_orders(request):
    sf = request.GET.get('status', 'all')
    qs = Order.objects.select_related('user', 'delivery_area').prefetch_related('items')
    filters = {
        'paid':       dict(payment_status='paid'),
        'preparing':  dict(delivery_status='preparing'),
        'on_the_way': dict(delivery_status='on_the_way'),
        'delivered':  dict(delivery_status='delivered'),
    }
    if sf in filters:
        qs = qs.filter(**filters[sf])
    return render(request, 'admin_panel/orders.html', {'orders': qs, 'status_filter': sf})


@admin_required
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_panel/users.html', {'users': users})


@admin_required
@require_POST
def update_user_role(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.role = request.POST.get('role', 'customer')
    user.save()
    messages.success(request, f"{user.first_name or user.username} → {user.role}.")
    return redirect('admin_users')


@admin_required
def admin_areas(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = request.POST.get('name', '').strip()
            fee  = request.POST.get('delivery_fee', 100)
            if name:
                DeliveryArea.objects.get_or_create(name=name, defaults={'delivery_fee': fee})
                messages.success(request, f'Area "{name}" added!')
        elif action == 'update':
            area             = get_object_or_404(DeliveryArea, id=request.POST['area_id'])
            area.name        = request.POST.get('name', area.name).strip()
            area.delivery_fee = float(request.POST.get('delivery_fee', area.delivery_fee))
            area.is_active   = request.POST.get('is_active') == '1'
            area.save()
            messages.success(request, 'Area updated!')
        return redirect('admin_areas')
    return render(request, 'admin_panel/areas.html', {'areas': DeliveryArea.objects.all()})


@admin_required
@require_POST
def delete_area(request, area_id):
    area = get_object_or_404(DeliveryArea, id=area_id)
    area.delete()
    messages.success(request, f'Area "{area.name}" deleted.')
    return redirect('admin_areas')


# ── KITCHEN ───────────────────────────────────────────────────────────────────

@kitchen_required
def kitchen_dashboard(request):
    orders = Order.objects.filter(
        payment_status='paid', delivery_status='pending'
    ).prefetch_related('items').select_related('user', 'delivery_area').order_by('created_at')
    return render(request, 'kitchen/dashboard.html', {'orders': orders})


@kitchen_required
@require_POST
def mark_preparing(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delivery_status = 'preparing'
    order.save()
    messages.success(request, f'Order {order.order_number} → Preparing.')
    return redirect('kitchen_dashboard')


# ── DELIVERY ──────────────────────────────────────────────────────────────────

@delivery_required
def delivery_dashboard(request):
    orders = Order.objects.filter(
        payment_status='paid', delivery_status__in=['preparing', 'on_the_way']
    ).prefetch_related('items').select_related('user', 'delivery_area').order_by('created_at')
    return render(request, 'delivery/dashboard.html', {'orders': orders})


@delivery_required
@require_POST
def update_delivery_status(request, order_id):
    order      = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    if new_status in ('on_the_way', 'delivered'):
        order.delivery_status = new_status
        if new_status == 'delivered':
            order.delivered_at = timezone.now()
        order.save()
        messages.success(request, f'Order {order.order_number} → {new_status.replace("_", " ").title()}.')
    return redirect('delivery_dashboard')
