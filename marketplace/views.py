import random
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg, F
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.conf import settings

from products.models import Product, Category, Review, Wishlist, Order, OrderItem, Subscriber, SellerProfile, Payout, SellerApplication, ContentReport


def login_view(request):
    """Custom login view with proper error handling."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'auth/login.html', {'form_data': request.POST})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next', '')
            if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return render(request, 'auth/login.html', {'form_data': request.POST})

    return render(request, 'auth/login.html')


def home(request):
    """Display the home page with featured products, categories, and sections."""
    featured_products = Product.objects.filter(status=True, is_featured=True)[:8]
    bestsellers = Product.objects.filter(status=True, is_bestseller=True)[:8]
    new_arrivals = Product.objects.filter(status=True, is_new_arrival=True)[:8]
    flash_sale = Product.objects.filter(status=True, is_flash_sale=True, discount_price__isnull=False)[:6]
    all_products = Product.objects.filter(status=True)[:12]
    categories = Category.objects.filter(is_active=True)[:8]
    hero_pool = list(Product.objects.filter(status=True, product_image__isnull=False).order_by('-sold_count')[:30])
    random.shuffle(hero_pool)
    hero_products = hero_pool[:12]

    context = {
        'featured_products': featured_products,
        'bestsellers': bestsellers,
        'new_arrivals': new_arrivals,
        'flash_sale': flash_sale,
        'all_products': all_products,
        'categories': categories,
        'hero_products': hero_products,
    }
    return render(request, 'home/home.html', context)


def register_view(request):
    """User registration with form validation."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        from django.contrib.auth.models import User
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        errors = []
        if not username:
            errors.append('Username is required.')
        if not email:
            errors.append('Email is required.')
        if password != password2:
            errors.append('Passwords do not match.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already taken.')
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'auth/register.html', {
                'form_data': request.POST
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        login(request, user)
        messages.success(request, f'Welcome to Islington Marketplace, {user.first_name or user.username}!')
        return redirect('home')

    return render(request, 'auth/register.html')


def logout_view(request):
    """Custom logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def dashboard_view(request):
    """User dashboard overview."""
    user_orders = Order.objects.filter(user=request.user)
    recent_orders = user_orders[:5]
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist_count = wishlist.products.count()
    except Wishlist.DoesNotExist:
        wishlist_count = 0

    context = {
        'recent_orders': recent_orders,
        'total_orders': user_orders.count(),
        'active_orders': user_orders.exclude(status='delivered').exclude(status='cancelled').count(),
        'wishlist_count': wishlist_count,
        'review_count': Review.objects.filter(user=request.user).count(),
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def dashboard_profile(request):
    """User profile management."""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('dashboard_profile')
    return render(request, 'dashboard/profile.html')


@login_required
def dashboard_orders(request):
    """User order history."""
    orders = Order.objects.filter(user=request.user)
    paginator = Paginator(orders, 10)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    return render(request, 'dashboard/orders.html', {'orders': orders})


@login_required
def dashboard_wishlist(request):
    """User wishlist."""
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        products = wishlist.products.all()
    except Wishlist.DoesNotExist:
        products = []
    return render(request, 'dashboard/wishlist.html', {'products': products})


@login_required
def dashboard_reviews(request):
    """User reviews."""
    reviews = Review.objects.filter(user=request.user)
    return render(request, 'dashboard/reviews.html', {'reviews': reviews})


@login_required
def dashboard_settings(request):
    """User settings."""
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'New password must be at least 8 characters.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Password updated successfully! Please log in again.')
                return redirect('login')
        else:
            messages.success(request, 'Settings updated successfully!')
        return redirect('dashboard_settings')
    return render(request, 'dashboard/settings.html')


@login_required
def dashboard_earnings(request):
    """Seller earnings dashboard."""
    app = SellerApplication.objects.filter(user=request.user, status='approved').first()
    if not app:
        messages.info(request, 'You need to become a seller first.')
        return redirect('become_seller')
    profile, _ = SellerProfile.objects.get_or_create(user=request.user)

    # Get sold items for this seller
    sold_items = OrderItem.objects.filter(
        product__seller=request.user,
        order__payment_status='completed'
    ).select_related('order', 'product').order_by('-order__created_at')

    # Payout history
    payouts = Payout.objects.filter(seller=request.user).order_by('-created_at')[:20]

    # Monthly earnings breakdown
    from django.db.models import Sum, F
    monthly_earnings = sold_items.values('order__created_at__year', 'order__created_at__month').annotate(
        total=Sum(F('price') * F('quantity'))
    ).order_by('-order__created_at__year', '-order__created_at__month')[:6]

    # Platform commission
    commission_amount = float(profile.pending_balance) * float(profile.commission_rate) / 100

    context = {
        'profile': profile,
        'sold_items': sold_items[:20],
        'payouts': payouts,
        'monthly_earnings': monthly_earnings,
        'total_earnings': profile.total_earnings,
        'total_paid_out': profile.total_paid_out,
        'pending_balance': profile.pending_balance,
        'commission_rate': profile.commission_rate,
        'commission_amount': commission_amount,
        'net_pending': float(profile.pending_balance) - commission_amount,
        'total_orders': sold_items.count(),
    }
    return render(request, 'dashboard/earnings.html', context)


@login_required
def dashboard_payment_settings(request):
    """Seller payment settings - eSewa/Khalti/Bank info."""
    app = SellerApplication.objects.filter(user=request.user, status='approved').first()
    if not app:
        messages.info(request, 'You need to become a seller first.')
        return redirect('become_seller')
    profile, _ = SellerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile.esewa_number = request.POST.get('esewa_number', '').strip()
        profile.khalti_number = request.POST.get('khalti_number', '').strip()
        profile.bank_name = request.POST.get('bank_name', '').strip()
        profile.bank_account = request.POST.get('bank_account', '').strip()
        profile.bank_branch = request.POST.get('bank_branch', '').strip()
        profile.preferred_method = request.POST.get('preferred_method', 'esewa')
        profile.save()
        messages.success(request, 'Payment settings updated successfully!')
        return redirect('dashboard_payment_settings')

    context = {
        'profile': profile,
    }
    return render(request, 'dashboard/payment_settings.html', context)


def search_view(request):
    """Search products with filtering."""
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category')
    sort = request.GET.get('sort', 'newest')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    rating = request.GET.get('rating')

    products = Product.objects.filter(status=True)
    active_filters = []

    if query:
        products = products.filter(
            Q(product_name__icontains=query) |
            Q(product_description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query)
        )

    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)
            products = products.filter(category=category)
        except Category.DoesNotExist:
            pass

    if min_price:
        products = products.filter(price__gte=min_price)
        active_filters.append(f'Min Rs. {min_price}')
    if max_price:
        products = products.filter(price__lte=max_price)
        active_filters.append(f'Max Rs. {max_price}')
    if rating:
        products = products.annotate(avg_rating=Avg('reviews__rating')).filter(avg_rating__gte=rating)
        active_filters.append(f'{rating}+ Stars')

    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'rating':
        if not rating:
            products = products.annotate(avg_rating=Avg('reviews__rating'))
        products = products.order_by('-avg_rating')
    elif sort == 'popular':
        products = products.order_by('-sold_count')
    else:
        products = products.order_by('-created_at')

    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)

    categories = Category.objects.filter(is_active=True)

    total_count = paginator.count

    if active_filters:
        hero_context = {
            'badge': 'Filtered Results',
            'title': ' + '.join(active_filters),
            'subtitle': f'{total_count} products match your selected filters.',
            'icon': 'fa-filter',
        }
    elif query:
        hero_context = {
            'badge': 'Search Results',
            'title': f'\u201c{query}\u201d',
            'subtitle': f'Showing {total_count} matching product{"" if total_count == 1 else "s"}.',
            'icon': 'fa-magnifying-glass',
        }
    else:
        hero_context = {
            'badge': 'Search',
            'title': 'Search Products',
            'subtitle': 'Find what you\u2019re looking for.',
            'icon': 'fa-magnifying-glass',
        }

    context = {
        'products': products,
        'query': query,
        'categories': categories,
        'selected_category': category_slug,
        'sort': sort,
        'min_price': min_price,
        'max_price': max_price,
        'rating': rating,
        'hero_context': hero_context,
        'product_count': total_count,
    }
    return render(request, 'products/search_results.html', context)


def search_suggestions(request):
    """API endpoint for live search suggestions."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'suggestions': []})

    products = Product.objects.filter(
        Q(product_name__icontains=query),
        status=True
    )[:8]

    suggestions = []
    for product in products:
        suggestions.append({
            'id': product.id,
            'name': product.product_name,
            'price': product.effective_price,
            'image': product.product_image.url if product.product_image else '',
            'category': product.category.name,
            'url': f'/products/{product.id}/',
        })

    categories = Category.objects.filter(name__icontains=query, is_active=True)[:4]
    for cat in categories:
        suggestions.append({
            'type': 'category',
            'name': cat.name,
            'url': f'/products/?category={cat.slug}',
        })

    return JsonResponse({'suggestions': suggestions})


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    """Toggle a product in the user's wishlist. Returns JSON for AJAX requests."""
    product = get_object_or_404(Product, id=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

    if wishlist.products.filter(id=product_id).exists():
        wishlist.products.remove(product)
        added = False
        message = f'{product.product_name} removed from wishlist.'
    else:
        wishlist.products.add(product)
        added = True
        message = f'{product.product_name} added to wishlist.'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'added': added,
            'message': message,
            'wishlist_count': wishlist.products.count(),
        })

    messages.success(request, message)
    return redirect('product_detail', id=product_id)


@require_POST
def subscribe_view(request):
    """Handle newsletter subscription via POST."""
    email = request.POST.get('email', '').strip()

    if not email:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Email is required.'})
        messages.error(request, 'Email is required.')
        from urllib.parse import urlparse
        referer = request.META.get('HTTP_REFERER', '')
        path = urlparse(referer).path if referer else ''
        return redirect(path if path.startswith('/') else 'home')

    if Subscriber.objects.filter(email=email).exists():
        subscriber = Subscriber.objects.get(email=email)
        if subscriber.is_active:
            msg = 'You are already subscribed!'
        else:
            subscriber.is_active = True
            subscriber.save()
            msg = 'Welcome back! Your subscription has been reactivated.'
    else:
        Subscriber.objects.create(email=email)
        msg = 'Thank you for subscribing!'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg})

    messages.success(request, msg)
    from urllib.parse import urlparse
    referer = request.META.get('HTTP_REFERER', '')
    path = urlparse(referer).path if referer else ''
    return redirect(path if path.startswith('/') else 'home')


def about_view(request):
    """Display the About Us page."""
    return render(request, 'pages/about.html')


def contact_view(request):
    """Display the Contact page."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not name or not email or not message:
            messages.error(request, 'Please fill in all required fields.')
        else:
            messages.success(request, 'Thank you for your message! We will get back to you soon.')

        return redirect('contact')

    return render(request, 'pages/contact.html')


@login_required
def checkout_view(request):
    """Display and process the checkout page."""
    from cart.views import get_or_create_cart
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product', 'product__category').all()

    if not items.exists():
        messages.warning(request, 'Your cart is empty. Add some products before checking out.')
        return redirect('cart_detail')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        province = request.POST.get('province', '').strip()
        city = request.POST.get('city', '').strip()
        ward = request.POST.get('ward', '').strip()
        municipality = request.POST.get('municipality', '').strip()
        street_address = request.POST.get('street_address', '').strip()
        shipping_address = request.POST.get('shipping_address', '').strip()
        payment_method = request.POST.get('payment_method', 'cod')
        notes = request.POST.get('notes', '').strip()

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not phone or len(phone) != 10 or not phone.isdigit():
            errors.append('Phone number must be exactly 10 digits.')
        if not email or '@' not in email:
            errors.append('Valid email is required.')
        if not province:
            errors.append('Please select a province.')
        if not city:
            errors.append('District is required.')
        if not ward:
            errors.append('Ward number is required.')
        if not municipality:
            errors.append('Municipality/VDC is required.')
        if not street_address:
            errors.append('Street address is required.')

        if payment_method == 'card':
            card_number = request.POST.get('card_number', '').replace(' ', '').strip()
            card_expiry = request.POST.get('card_expiry', '').strip()
            card_cvv = request.POST.get('card_cvv', '').strip()
            card_name = request.POST.get('card_name', '').strip()
            if not card_number or len(card_number) < 13 or len(card_number) > 19:
                errors.append('Valid card number is required.')
            if not card_expiry or len(card_expiry) != 5:
                errors.append('Valid expiry date (MM/YY) is required.')
            if not card_cvv or len(card_cvv) < 3:
                errors.append('Valid CVV is required.')
            if not card_name:
                errors.append('Name on card is required.')

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'checkout/checkout.html', {
                'cart': cart, 'items': items, 'subtotal': cart.subtotal,
                'coupon_discount': cart.coupon_discount, 'total': cart.total_price,
                'savings': cart.savings,
            })

        # Build full shipping address from parts
        shipping_address = f'{street_address}, Ward {ward}, {municipality}, {city}, {province}'

        order = Order.objects.create(
            user=request.user,
            total_amount=cart.total_price,
            shipping_address=shipping_address,
            phone=phone,
            email=email,
            full_name=full_name,
            province=province,
            city=city,
            ward=ward,
            payment_method=payment_method,
            payment_status='pending',
            notes=notes,
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.discount_price or item.product.price,
                quantity=item.quantity,
            )
            Product.objects.filter(id=item.product.id).update(stock=F('stock') - item.quantity)

        if payment_method in ('khalti', 'esewa'):
            request.session['pending_order_id'] = order.id
            return redirect('khalti_payment' if payment_method == 'khalti' else 'esewa_payment', order_id=order.id)

        cart.items.all().delete()
        cart.coupon = None
        cart.save()

        if payment_method == 'card':
            order.transaction_id = 'CARD' + str(order.id)
            order.payment_status = 'completed'
            order.status = 'processing'
            order.save()
            messages.success(request, f'Payment successful! Order {order.order_number} confirmed.')
            return redirect('order_confirmation', order_id=order.id)
        else:
            order.payment_status = 'pending'
            order.save()
            messages.success(request, f'Order {order.order_number} placed successfully! Pay on delivery.')
            return redirect('order_confirmation', order_id=order.id)

    context = {
        'cart': cart,
        'items': items,
        'subtotal': cart.subtotal,
        'coupon_discount': cart.coupon_discount,
        'total': cart.total_price,
        'savings': cart.savings,
        'khalti_public_key': settings.KHALTI_PUBLIC_KEY,
    }
    return render(request, 'checkout/checkout.html', context)


@login_required
def order_confirmation_view(request, order_id):
    """Display order confirmation page."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'checkout/order_confirmation.html', {'order': order})


@login_required
def esewa_payment_view(request, order_id):
    """Redirect to eSewa payment gateway."""
    order = get_object_or_404(Order, id=order_id, user=request.user, payment_method='esewa')
    if order.payment_status == 'completed':
        messages.info(request, 'This order has already been paid.')
        return redirect('order_confirmation', order_id=order.id)

    # eSewa gateway config (sandbox)
    esewa_config = {
        'amt': float(order.total_amount),
        'pdc': 0,
        'psc': 0,
        'txAmt': 0,
        'tAmt': float(order.total_amount),
        'pid': order.order_number,
        'scd': 'EPAYTEST',
        'su': request.build_absolute_uri(f'/payment/esewa/verify/{order.id}/'),
        'fu': request.build_absolute_uri(f'/payment/esewa/fail/{order.id}/'),
    }

    return render(request, 'checkout/esewa_payment.html', {
        'order': order,
        'esewa_config': esewa_config,
    })


@login_required
def esewa_verify_view(request, order_id):
    """Verify eSewa payment and update order."""
    order = get_object_or_404(Order, id=order_id, user=request.user, payment_method='esewa')

    ref_id = request.GET.get('refId', '').strip()
    if not ref_id:
        order.payment_status = 'failed'
        order.save()
        messages.error(request, 'eSewa payment failed: No reference ID received. Please try again.')
        return redirect('esewa_payment', order_id=order.id)

    # In production, verify refId with eSewa API
    # For demo: refId "fail" triggers failure, anything else succeeds
    if ref_id == 'fail':
        order.payment_status = 'failed'
        order.save()
        messages.error(request, 'eSewa payment verification failed. Please try again.')
        return redirect('esewa_payment', order_id=order.id)

    order.payment_status = 'completed'
    order.transaction_id = 'ESW' + ref_id
    order.status = 'processing'
    order.save()
    messages.success(request, f'eSewa payment successful! Order {order.order_number} confirmed.')
    return redirect('order_confirmation', order_id=order.id)


@login_required
def esewa_fail_view(request, order_id):
    """Handle eSewa payment failure."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.payment_status = 'failed'
    order.save()
    messages.error(request, 'eSewa payment was cancelled. You can retry or choose a different payment method.')
    return redirect('esewa_payment', order_id=order.id)


@login_required
@require_POST
def khalti_initiate_view(request):
    """
    JSON API endpoint to initiate Khalti ePayment.

    Accepts POST with checkout form data, creates the order,
    calls the official Khalti API, and returns JSON:
    { "success": true, "payment_url": "...", "pidx": "..." }
    """
    from cart.views import get_or_create_cart

    cart = get_or_create_cart(request)
    items = cart.items.select_related('product', 'product__category').all()

    if not items.exists():
        return JsonResponse({'success': False, 'error': 'Your cart is empty.'}, status=400)

    try:
        body = json.loads(request.body) if request.content_type == 'application/json' else request.POST
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid request data.'}, status=400)

    full_name = body.get('full_name', '').strip()
    phone = body.get('phone', '').strip()
    email = body.get('email', '').strip()
    province = body.get('province', '').strip()
    city = body.get('city', '').strip()
    ward = body.get('ward', '').strip()
    municipality = body.get('municipality', '').strip()
    street_address = body.get('street_address', '').strip()
    notes = body.get('notes', '').strip()

    errors = []
    if not full_name:
        errors.append('Full name is required.')
    if not phone or len(phone) != 10 or not phone.isdigit():
        errors.append('Phone number must be exactly 10 digits.')
    if not email or '@' not in email:
        errors.append('Valid email is required.')
    if not province:
        errors.append('Province is required.')
    if not city:
        errors.append('District is required.')
    if not ward:
        errors.append('Ward number is required.')
    if not municipality:
        errors.append('Municipality/VDC is required.')
    if not street_address:
        errors.append('Street address is required.')

    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    stock_errors = []
    for item in items:
        if item.product.stock < item.quantity:
            stock_errors.append(f'"{item.product.product_name}" is out of stock (requested: {item.quantity}, available: {item.product.stock}).')
    if stock_errors:
        return JsonResponse({'success': False, 'errors': stock_errors}, status=400)

    shipping_address = f'{street_address}, Ward {ward}, {municipality}, {city}, {province}'

    order = Order.objects.create(
        user=request.user,
        total_amount=cart.total_price,
        shipping_address=shipping_address,
        phone=phone,
        email=email,
        full_name=full_name,
        province=province,
        city=city,
        ward=ward,
        payment_method='khalti',
        payment_status='pending',
        notes=notes,
    )

    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            price=item.product.discount_price or item.product.price,
            quantity=item.quantity,
        )
        Product.objects.filter(id=item.product.id).update(stock=F('stock') - item.quantity)

    request.session['pending_order_id'] = order.id

    try:
        from marketplace.services.khalti_service import initiate_payment
        result = initiate_payment(order, request)
    except ValueError as e:
        for item in items:
            Product.objects.filter(id=item.product.id).update(stock=F('stock') + item.quantity)
        order.payment_status = 'failed'
        order.save()
        return JsonResponse({'success': False, 'error': str(e)}, status=402)

    Order.objects.filter(id=order.id).update(transaction_id=result['pidx'])

    return JsonResponse({
        'success': True,
        'payment_url': result['payment_url'],
        'pidx': result['pidx'],
    })


@login_required
def khalti_payment_view(request, order_id):
    """Initiate Khalti payment by calling the API and redirecting to Khalti."""
    order = get_object_or_404(Order, id=order_id, user=request.user, payment_method='khalti')

    if order.payment_status == 'completed':
        messages.info(request, 'This order has already been paid.')
        return redirect('order_confirmation', order_id=order.id)

    if not settings.KHALTI_SECRET_KEY:
        messages.error(request, 'Khalti payment is not configured. Please try a different payment method.')
        return redirect('checkout')

    try:
        from marketplace.services.khalti_service import initiate_payment
        result = initiate_payment(order, request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('checkout')

    Order.objects.filter(id=order.id).update(transaction_id=result['pidx'])

    return render(request, 'checkout/khalti_payment.html', {
        'order': order,
        'khalti_redirect_url': result['payment_url'],
    })


@login_required
def khalti_verify_view(request, order_id):
    """Handle return from Khalti after payment attempt."""
    from cart.views import get_or_create_cart

    pidx = request.GET.get('pidx')
    order = get_object_or_404(Order, id=order_id, user=request.user, payment_method='khalti')

    if not pidx:
        messages.error(request, 'Invalid Khalti response. No payment reference found.')
        return redirect('checkout')

    if order.transaction_id and order.transaction_id != pidx:
        messages.error(request, 'Payment reference does not match this order.')
        return redirect('checkout')

    try:
        from marketplace.services.khalti_service import verify_payment
        result = verify_payment(pidx)
    except ValueError as e:
        messages.error(request, str(e))
        order.payment_status = 'failed'
        order.save()
        _restore_stock(order)
        return redirect('checkout')

    khalti_status = result.get('status', '').upper()
    txn_id = result.get('transaction_id', '')
    paid_amount = result.get('amount', 0)
    expected_amount = int(float(order.total_amount) * 100)

    if paid_amount != expected_amount:
        order.payment_status = 'failed'
        order.save()
        _restore_stock(order)
        messages.error(request, 'Payment amount mismatch. Please contact support.')
        return redirect('checkout')

    if khalti_status == 'COMPLETE':
        order.payment_status = 'completed'
        order.transaction_id = txn_id or pidx
        order.status = 'processing'
        order.save()
        _clear_cart(request)
        messages.success(request, f'Khalti payment successful! Order {order.order_number} confirmed.')
        return redirect('order_confirmation', order_id=order.id)
    elif khalti_status == 'PENDING':
        messages.warning(request, 'Your Khalti payment is pending. We will confirm shortly.')
        order.payment_status = 'pending'
        order.save()
        return redirect('order_confirmation', order_id=order.id)
    else:
        order.payment_status = 'failed'
        order.save()
        _restore_stock(order)
        messages.error(request, f'Khalti payment failed (status: {khalti_status}). Please try again.')
        return redirect('checkout')


def _restore_stock(order):
    """Restore stock for all items in an order."""
    for item in order.items.select_related('product').all():
        Product.objects.filter(id=item.product.id).update(stock=F('stock') + item.quantity)


def _clear_cart(request):
    """Clear the user's cart after successful payment."""
    from cart.views import get_or_create_cart
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    cart.coupon = None
    cart.save()


@login_required
def khalti_failure_view(request, order_id):
    """Handle Khalti payment failure."""
    order = get_object_or_404(Order, id=order_id, user=request.user, payment_method='khalti')
    if order.payment_status != 'failed':
        order.payment_status = 'failed'
        order.save()
        _restore_stock(order)
    messages.error(request, 'Khalti payment failed. Please try again or choose a different payment method.')
    return redirect('checkout')


@login_required
def khalti_cancel_view(request, order_id):
    """Handle Khalti payment cancellation."""
    order = get_object_or_404(Order, id=order_id, user=request.user, payment_method='khalti')
    if order.payment_status != 'failed':
        order.payment_status = 'failed'
        order.save()
        _restore_stock(order)
    messages.warning(request, 'You cancelled the Khalti payment. You can try again or choose a different payment method.')
    return redirect('checkout')


# ========== SELLER APPLICATION ==========

def become_seller(request):
    """Seller application page — simplified: just personal info."""
    if not request.user.is_authenticated:
        messages.info(request, 'Please log in or create an account to apply as a seller.')
        return redirect('login')

    existing = SellerApplication.objects.filter(user=request.user).first()
    if existing and existing.status in ('approved', 'under_review'):
        messages.info(request, f'Your application is {existing.get_status_display().lower()}.')
        return redirect('dashboard')

    if request.method == 'POST':
        required = ['full_name', 'phone', 'email', 'address', 'city', 'province']
        errors = []
        for field in required:
            if not request.POST.get(field, '').strip():
                errors.append(f'{field.replace("_", " ").title()} is required.')

        if not request.POST.get('agreed_to_terms'):
            errors.append('You must agree to the Terms of Service, Privacy Policy, and Seller Guidelines.')

        if errors:
            for err in errors:
                messages.error(request, err)
            return redirect('become_seller')

        app, created = SellerApplication.objects.get_or_create(user=request.user)
        app.full_name = request.POST['full_name'].strip()
        app.phone = request.POST['phone'].strip()
        app.email = request.POST['email'].strip()
        app.address = request.POST['address'].strip()
        app.city = request.POST['city'].strip()
        app.province = request.POST['province'].strip()
        app.business_type = 'individual'
        app.selling_reason = 'N/A'
        app.document_type = 'citizenship'
        app.document_number = 'pending'
        app.agreed_to_terms = True
        app.status = 'approved'
        app.save()

        messages.success(request, 'Your seller account is now active! You can start listing products right away.')
        return redirect('dashboard')

    context = {
        'existing_app': existing,
    }
    return render(request, 'seller/become_seller.html', context)


def seller_application_status(request):
    """Check seller application status."""
    if not request.user.is_authenticated:
        return redirect('login')
    app = SellerApplication.objects.filter(user=request.user).first()
    return render(request, 'seller/application_status.html', {'application': app})


# ========== AGE VERIFICATION ==========

def age_verify(request):
    """Age verification gate for 18+ content."""
    if request.method == 'POST':
        dob = request.POST.get('date_of_birth', '')
        if dob:
            try:
                from datetime import date
                birth = date.fromisoformat(dob)
                today = date.today()
                age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                if age >= 18:
                    request.session['age_verified'] = True
                    request.session['age_verified_at'] = str(today)
                    next_url = request.GET.get('next', '/')
                    if not next_url.startswith('/') or next_url.startswith('//'):
                        next_url = '/'
                    return redirect(next_url)
                else:
                    messages.error(request, 'You must be 18 or older to access this content.')
            except ValueError:
                messages.error(request, 'Please enter a valid date.')
    return render(request, 'seller/age_verify.html')


# ========== CONTENT REPORTING ==========

@login_required
def report_content(request):
    """Report inappropriate content."""
    if request.method != 'POST':
        return redirect('home')

    product_id = request.POST.get('product_id')
    seller_id = request.POST.get('seller_id')
    reason = request.POST.get('reason', '')
    description = request.POST.get('description', '').strip()

    if not reason:
        messages.error(request, 'Please select a reason for the report.')
        return redirect('home')

    report = ContentReport(
        reporter=request.user,
        reason=reason,
        description=description,
        evidence_image=request.FILES.get('evidence_image'),
    )
    if product_id and product_id.isdigit():
        if Product.objects.filter(id=int(product_id)).exists():
            report.product_id = int(product_id)
    if seller_id and seller_id.isdigit():
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(id=int(seller_id)).exists():
            report.seller_id = int(seller_id)
    report.save()

    messages.success(request, 'Thank you for your report. Our team will review it shortly.')
    return redirect('home')


# ========== LEGAL / POLICY PAGES ==========

def privacy_policy(request):
    """Privacy policy page."""
    return render(request, 'legal/privacy_policy.html')


def terms_of_service(request):
    """Terms of service page."""
    return render(request, 'legal/terms_of_service.html')


def seller_guidelines(request):
    """Seller guidelines and policies."""
    return render(request, 'legal/seller_guidelines.html')


def prohibited_items(request):
    """List of prohibited and restricted items."""
    return render(request, 'legal/prohibited_items.html')


def content_policy(request):
    """Content moderation policy."""
    return render(request, 'legal/content_policy.html')
