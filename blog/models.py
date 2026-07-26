from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    excerpt = models.TextField(max_length=300, help_text='Short summary shown on blog listing')
    content = models.TextField()
    featured_image = models.URLField(blank=True, help_text='URL of the blog post image')
    category = models.CharField(max_length=50, blank=True, choices=[
        ('', 'Uncategorized'),
        ('news', 'News'),
        ('tips', 'Tips & Guides'),
        ('deals', 'Deals & Offers'),
        ('lifestyle', 'Lifestyle'),
    ])
    is_published = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
