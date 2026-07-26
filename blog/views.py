from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import F

from .models import BlogPost


def blog(request):
    """Display all published blog posts."""
    posts = BlogPost.objects.filter(is_published=True)
    paginator = Paginator(posts, 6)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    return render(request, 'blog/blog.html', {'posts': posts})


def blog_detail(request, slug):
    """Display a single blog post."""
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    BlogPost.objects.filter(id=post.id).update(views_count=F('views_count') + 1)
    related = BlogPost.objects.filter(is_published=True, category=post.category).exclude(id=post.id)[:3]
    return render(request, 'blog/blog_detail.html', {'post': post, 'related': related})
