from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg

from .models import Category, Product, Review


def products(request):
    """
    Display all products with dynamic marketplace hero.
    Supports ?category=<slug>, ?q=<search>,
    ?min_price, ?max_price, ?rating query parameters.
    """
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q', '').strip()
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    rating = request.GET.get('rating')

    product_list = Product.objects.filter(status=True)
    active_filters = []

    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)

            # Age verification for restricted categories
            if category.slug == 'alcohol' and not request.session.get('age_verified'):
                return redirect(f'/age-verify/?next={request.path}')

            product_list = product_list.filter(category=category)
            hero_context = {
                'badge': 'Category',
                'title': category.name,
                'subtitle': f'Discover the best {category.name} available from trusted sellers.',
                'icon': 'fa-tag',
            }
        except Category.DoesNotExist:
            hero_context = {
                'badge': 'Collection',
                'title': 'All Products',
                'subtitle': 'Browse our complete collection of quality items.',
                'icon': 'fa-store',
            }
    elif search_query:
        product_list = product_list.filter(
            Q(product_name__icontains=search_query) |
            Q(product_description__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(brand__name__icontains=search_query)
        )
        hero_context = {
            'badge': 'Search Results',
            'title': f'\u201c{search_query}\u201d',
            'subtitle': f'Showing {product_list.count()} matching product{"" if product_list.count() == 1 else "s"}.',
            'icon': 'fa-magnifying-glass',
        }
    else:
        hero_context = {
            'badge': 'Collection',
            'title': 'All Products',
            'subtitle': 'Browse our complete collection of quality items.',
            'icon': 'fa-store',
        }

    if min_price:
        product_list = product_list.filter(price__gte=min_price)
        active_filters.append(f'Min Rs. {min_price}')
    if max_price:
        product_list = product_list.filter(price__lte=max_price)
        active_filters.append(f'Max Rs. {max_price}')
    if rating:
        product_list = product_list.annotate(avg_rating=Avg('reviews__rating')).filter(avg_rating__gte=rating)
        active_filters.append(f'{rating}+ Stars')

    if active_filters:
        hero_context = {
            'badge': 'Filtered Results',
            'title': ' + '.join(active_filters),
            'subtitle': f'{product_list.count()} products match your selected filters.',
            'icon': 'fa-filter',
        }

    categories = Category.objects.filter(is_active=True)

    context = {
        'products': product_list,
        'categories': categories,
        'selected_category': category_slug,
        'hero_context': hero_context,
        'product_count': product_list.count(),
    }
    return render(request, 'products/products.html', context)


def product_detail(request, id):
    """Display detailed view of a single product with reviews and related products."""
    product = get_object_or_404(Product, id=id)

    # Age verification for restricted categories
    if product.category and product.category.slug == 'alcohol' and not request.session.get('age_verified'):
        return redirect(f'/age-verify/?next={request.path}')

    # Increment view count
    from django.db.models import F
    Product.objects.filter(id=id).update(view_count=F('view_count') + 1)

    # Handle review submission
    if request.method == 'POST' and request.user.is_authenticated:
        rating = request.POST.get('rating', '').strip()
        title = request.POST.get('title', '').strip()
        comment = request.POST.get('comment', '').strip()

        if not rating or not rating.isdigit() or int(rating) < 1 or int(rating) > 5:
            messages.error(request, 'Please select a valid rating.')
            return redirect('product_detail', id=id)

        if not comment:
            messages.error(request, 'Please write a review comment.')
            return redirect('product_detail', id=id)

        Review.objects.create(
            product=product,
            user=request.user,
            rating=int(rating),
            title=title,
            comment=comment,
        )
        messages.success(request, 'Your review has been submitted successfully!')
        return redirect('product_detail', id=id)

    # Related products (same category, excluding current)
    related_products = Product.objects.filter(
        category=product.category,
        status=True
    ).exclude(id=product.id)[:4]

    # Rating distribution (5-star to 1-star percentages)
    total_reviews = product.review_count
    rating_distribution = []
    for star in range(5, 0, -1):
        count = product.reviews.filter(rating=star).count()
        rating_distribution.append(round((count / total_reviews * 100) if total_reviews > 0 else 0))

    context = {
        'product': product,
        'related_products': related_products,
        'rating_distribution': rating_distribution,
    }
    return render(request, 'products/details.html', context)
