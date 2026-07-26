from .models import Page


def nav_pages(request):
    """
    Context processor that makes all published pages available
    in every template via the 'nav_pages' variable.
    """
    nav_pages = Page.objects.filter(is_published=True).order_by('title')
    return {'nav_pages': nav_pages}
