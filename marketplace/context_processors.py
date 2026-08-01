from products.models import Cart, Wishlist, Subscriber


def cart_context(request):
    """Make cart and wishlist data available in all templates."""
    context = {
        'cart_item_count': 0,
        'wishlist_count': 0,
    }

    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            context['cart_item_count'] = cart.total_items
            context['cart_total'] = cart.total_price
        except Cart.DoesNotExist:
            pass

        try:
            wishlist = Wishlist.objects.get(user=request.user)
            context['wishlist_count'] = wishlist.products.count()
        except Wishlist.DoesNotExist:
            pass
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.get(session_key=session_key)
                context['cart_item_count'] = cart.total_items
                context['cart_total'] = cart.total_price
            except Cart.DoesNotExist:
                pass

    return context


def notifications_context(request):
    """Make notification messages available for toast notifications."""
    from django.contrib.messages import get_messages
    messages = []
    storage = get_messages(request)
    for message in storage:
        messages.append({
            'tags': message.tags,
            'message': str(message),
        })
    return {'toast_messages': messages}


def newsletter_context(request):
    """Make subscriber data available globally for the newsletter section.

    The subscribed state is bound to the logged-in user's email, falling back
    to the email subscribed within the current anonymous session. This keeps
    the state correct per user instead of relying on a global browser flag.
    """
    subscribed = False
    email = ''

    if request.user.is_authenticated:
        email = request.user.email or ''
        subscribed = bool(email) and Subscriber.objects.filter(
            email__iexact=email, is_active=True
        ).exists()
    else:
        email = request.session.get('newsletter_email', '') or ''
        if email:
            subscribed = Subscriber.objects.filter(
                email__iexact=email, is_active=True
            ).exists()

    return {
        'subscriber_count': Subscriber.objects.filter(is_active=True).count(),
        'newsletter_subscribed': subscribed,
        'newsletter_email': email,
    }
