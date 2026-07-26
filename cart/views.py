"""
Shopping Cart views.

Handles adding, removing, updating items, coupon application,
and displaying the cart page. Works for both authenticated users
and anonymous users via session keys.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from products.models import Product, Cart, CartItem, Coupon


def get_or_create_cart(request):
    """
    Get or create a cart for the current user or anonymous session.
    If user logs in later, merge the session cart into their user cart.
    """
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Merge anonymous session cart if it exists
        session_key = request.session.session_key
        if session_key:
            try:
                anon_cart = Cart.objects.get(session_key=session_key, user=None)
                for item in anon_cart.items.all():
                    existing = CartItem.objects.filter(cart=cart, product=item.product).first()
                    if existing:
                        existing.quantity += item.quantity
                        existing.save()
                    else:
                        item.cart = cart
                        item.save()
                anon_cart.delete()
            except Cart.DoesNotExist:
                pass
        return cart
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key, user=None)
        return cart


@require_POST
def add_to_cart(request, product_id):
    """Add a product to the cart. Supports both AJAX and normal requests."""
    product = get_object_or_404(Product, id=product_id, status=True)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1
    cart = get_or_create_cart(request)

    if quantity < 1:
        quantity = 1
    if quantity > product.stock:
        quantity = product.stock

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        cart_item.quantity += quantity
        if cart_item.quantity > product.stock:
            cart_item.quantity = product.stock
        cart_item.save()
    else:
        cart_item.quantity = quantity
        cart_item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.product_name} added to cart.',
            'cart_total': cart.total_items,
            'cart_price': float(cart.total_price),
        })

    messages.success(request, f'{product.product_name} added to cart!')
    return redirect('cart_detail')


@require_POST
def remove_from_cart(request, item_id):
    """Remove an item from the cart."""
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = get_or_create_cart(request)

    if cart_item.cart.id != cart.id:
        messages.error(request, 'Invalid cart item.')
        return redirect('cart_detail')

    product_name = cart_item.product.product_name
    cart_item.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product_name} removed from cart.',
            'cart_total': cart.total_items,
            'cart_price': float(cart.total_price),
        })

    messages.success(request, f'{product_name} removed from cart.')
    return redirect('cart_detail')


@require_POST
def update_cart(request, item_id):
    """Update the quantity of a cart item."""
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart = get_or_create_cart(request)

    if cart_item.cart.id != cart.id:
        messages.error(request, 'Invalid cart item.')
        return redirect('cart_detail')

    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        quantity = 1
    if quantity > cart_item.product.stock:
        quantity = cart_item.product.stock

    cart_item.quantity = quantity
    cart_item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Cart updated.',
            'item_subtotal': float(cart_item.subtotal),
            'cart_total': cart.total_items,
            'cart_price': float(cart.total_price),
            'subtotal': float(cart.subtotal),
            'coupon_discount': float(cart.coupon_discount),
        })

    return redirect('cart_detail')


@require_POST
def apply_coupon(request):
    """Apply a coupon code to the cart."""
    code = request.POST.get('coupon_code', '').strip().upper()
    cart = get_or_create_cart(request)

    if not code:
        messages.error(request, 'Please enter a coupon code.')
        return redirect('cart_detail')

    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        messages.error(request, 'Invalid coupon code.')
        return redirect('cart_detail')

    if not coupon.is_valid:
        messages.error(request, 'This coupon is no longer valid or has expired.')
        return redirect('cart_detail')

    if cart.subtotal < coupon.min_purchase:
        messages.error(request, f'Minimum purchase of Rs. {coupon.min_purchase} required for this coupon.')
        return redirect('cart_detail')

    cart.coupon = coupon
    cart.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Coupon {coupon.code} applied!',
            'coupon_discount': float(cart.coupon_discount),
            'cart_price': float(cart.total_price),
            'subtotal': float(cart.subtotal),
        })

    messages.success(request, f'Coupon {coupon.code} applied! You save Rs. {cart.coupon_discount}.')
    return redirect('cart_detail')


@require_POST
def remove_coupon(request):
    """Remove the applied coupon from the cart."""
    cart = get_or_create_cart(request)
    cart.coupon = None
    cart.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Coupon removed.',
            'cart_price': float(cart.total_price),
            'subtotal': float(cart.subtotal),
        })

    messages.success(request, 'Coupon removed.')
    return redirect('cart_detail')


def cart_detail(request):
    """Display the shopping cart page."""
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product', 'product__category').all()

    # Check if coupon is still valid
    coupon_valid = True
    if cart.coupon and not cart.coupon.is_valid:
        coupon_valid = False
        messages.warning(request, f'Coupon {cart.coupon.code} is no longer valid and has been removed.')
        cart.coupon = None
        cart.save()

    context = {
        'cart': cart,
        'items': items,
        'subtotal': cart.subtotal,
        'coupon_discount': cart.coupon_discount,
        'total': cart.total_price,
        'savings': cart.savings,
        'coupon_valid': coupon_valid,
    }
    return render(request, 'cart/cart_detail.html', context)
