from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=25)
    slug = models.SlugField(max_length=50, unique=True, null=True, blank=True)
    description = models.TextField(blank=True, default='')
    icon = models.CharField(max_length=50, blank=True, default='fa-box')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def product_count(self):
        return self.product_set.filter(status=True).count()


class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    product_name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    price = models.FloatField()
    product_description = models.TextField()
    stock = models.IntegerField(default=1)
    status = models.BooleanField(default=0)
    product_image = models.ImageField(upload_to='products/images/', blank=True, null=True)

    discount_price = models.PositiveIntegerField(blank=True, null=True)
    quantity = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')

    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_flash_sale = models.BooleanField(default=False)
    flash_sale_end = models.DateTimeField(null=True, blank=True)
    sold_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.product_name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.product_name)
        super().save(*args, **kwargs)

    @property
    def discount_percentage(self):
        if self.discount_price and self.price > 0:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def effective_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0

    @property
    def review_count(self):
        return self.reviews.count()

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def stock_status(self):
        if self.stock == 0:
            return 'out_of_stock'
        elif self.stock <= 5:
            return 'low_stock'
        return 'in_stock'

    @property
    def primary_image(self):
        """Return the main product image, or the first gallery image, or None."""
        if self.product_image:
            return self.product_image
        first_extra = self.additional_images.first()
        if first_extra:
            return first_extra.image
        return None


class ProductImage(models.Model):
    """Additional images for a product (gallery)."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True, default='')
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f'Image for {self.product.product_name}'


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    image = models.ImageField(upload_to='reviews/', blank=True, null=True)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']

    def __str__(self):
        return f'{self.user.username} - {self.product.product_name} ({self.rating}*)'


class Coupon(models.Model):
    """Discount coupon that can be applied to carts during checkout."""
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text='Fixed amount discount')
    discount_percent = models.PositiveIntegerField(default=0, help_text='Percentage discount (0-100)')
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Minimum order amount required')
    max_uses = models.PositiveIntegerField(default=0, help_text='0 = unlimited uses')
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        from django.utils import timezone as tz
        now = tz.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        return True

    def apply_discount(self, total):
        """Calculate the discount amount on a given total."""
        if not self.is_valid:
            return 0
        if self.min_purchase and total < self.min_purchase:
            return 0
        if self.discount_percent > 0:
            return round(float(total) * self.discount_percent / 100, 2)
        return float(self.discount_amount)


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart {self.id}'

    @property
    def total_price(self):
        total = sum(item.subtotal for item in self.items.all())
        if self.coupon:
            discount = self.coupon.apply_discount(total)
            total = max(0, total - discount)
        return round(total, 2)

    @property
    def subtotal(self):
        """Total before coupon discount."""
        return sum(item.subtotal for item in self.items.all())

    @property
    def coupon_discount(self):
        """Amount deducted by coupon."""
        if self.coupon:
            return self.coupon.apply_discount(self.subtotal)
        return 0

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def savings(self):
        savings = 0
        for item in self.items.all():
            if item.product.discount_price:
                savings += (item.product.price - item.product.discount_price) * item.quantity
        return savings


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product']

    def __str__(self):
        return f'{self.quantity}x {self.product.product_name}'

    @property
    def subtotal(self):
        return self.product.effective_price * self.quantity


class Wishlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Wishlist of {self.user.username}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'),
        ('card', 'Credit/Debit Card'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    billing_address = models.TextField(blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    full_name = models.CharField(max_length=200, blank=True)
    province = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    ward = models.CharField(max_length=20, blank=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order {self.order_number}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            import random
            import string
            self.order_number = 'ORD' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity}x {self.product.product_name}'

    @property
    def subtotal(self):
        return self.price * self.quantity


class Subscriber(models.Model):
    """Email newsletter subscriber."""
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class SellerProfile(models.Model):
    """Payment and seller info for each user."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_profile')
    esewa_number = models.CharField(max_length=20, blank=True, default='', help_text='eSewa registered mobile number')
    khalti_number = models.CharField(max_length=20, blank=True, default='', help_text='Khalti registered mobile number')
    bank_name = models.CharField(max_length=100, blank=True, default='')
    bank_account = models.CharField(max_length=30, blank=True, default='')
    bank_branch = models.CharField(max_length=100, blank=True, default='')
    preferred_method = models.CharField(max_length=20, choices=[('esewa', 'eSewa'), ('khalti', 'Khalti'), ('bank', 'Bank Transfer')], default='esewa')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, help_text='Platform commission percentage')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - Seller Profile'

    @property
    def total_earnings(self):
        from django.db.models import Sum, F
        items = OrderItem.objects.filter(product__seller=self.user, order__payment_status='completed')
        return items.aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0

    @property
    def total_paid_out(self):
        from django.db.models import Sum
        return Payout.objects.filter(seller=self.user, status='completed').aggregate(total=Sum('amount'))['total'] or 0

    @property
    def pending_balance(self):
        return self.total_earnings - self.total_paid_out


class Payout(models.Model):
    """Tracks money paid out to sellers."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=[('esewa', 'eSewa'), ('khalti', 'Khalti'), ('bank', 'Bank Transfer')])
    account_number = models.CharField(max_length=30, help_text='eSewa/Khalti number or bank account')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference_id = models.CharField(max_length=100, blank=True, help_text='Transaction reference from payment gateway')
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payouts')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Payout Rs. {self.amount} to {self.seller.username} ({self.status})'


class SellerApplication(models.Model):
    """Seller application with KYC verification."""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_info', 'Needs More Information'),
    ]

    BUSINESS_TYPE_CHOICES = [
        ('individual', 'Individual / Sole Proprietor'),
        ('company', 'Registered Company'),
        ('partnership', 'Partnership Firm'),
    ]

    DOCUMENT_TYPE_CHOICES = [
        ('citizenship', 'Citizenship Certificate'),
        ('passport', 'Passport'),
        ('license', 'Driving License'),
        ('national_id', 'National ID Card'),
        ('pan', 'PAN Card'),
        ('business_reg', 'Business Registration Certificate'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_application')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Personal Info
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)

    # Business Info
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, default='individual')
    business_name = models.CharField(max_length=200, blank=True, default='')
    business_reg_number = models.CharField(max_length=100, blank=True, default='')
    pan_number = models.CharField(max_length=20, blank=True, default='')
    business_description = models.TextField(blank=True, default='')

    # What they want to sell
    product_categories = models.ManyToManyField(Category, blank=True)
    selling_reason = models.TextField(help_text='Why do you want to sell on Islington Marketplace?')
    estimated_monthly_sales = models.CharField(max_length=50, blank=True, default='')

    # Age Verification
    date_of_birth = models.DateField(help_text='Required for age-restricted categories', null=True, blank=True)
    is_age_verified = models.BooleanField(default=False)

    # KYC Document
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='citizenship')
    document_number = models.CharField(max_length=50)
    document_front = models.ImageField(upload_to='seller_docs/front/', blank=True, null=True)
    document_back = models.ImageField(upload_to='seller_docs/back/', blank=True, null=True)

    # Terms & Privacy
    agreed_to_terms = models.BooleanField(default=False)
    agreed_to_privacy = models.BooleanField(default=False)
    agreed_to_seller_policy = models.BooleanField(default=False)
    consent_to_data_processing = models.BooleanField(default=False)

    # Review
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    review_notes = models.TextField(blank=True, default='')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} - {self.get_status_display()}'

    @property
    def is_adult(self):
        """Check if applicant is 18+."""
        if not self.date_of_birth:
            return True
        from datetime import date
        today = date.today()
        return (today.year - self.date_of_birth.year -
                ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))) >= 18

    def save(self, *args, **kwargs):
        if self.is_adult:
            self.is_age_verified = True
        super().save(*args, **kwargs)


class ContentReport(models.Model):
    """User reports for inappropriate content."""
    REASON_CHOICES = [
        ('fraud', 'Fraud / Scam'),
        ('counterfeit', 'Counterfeit / Fake Product'),
        ('inappropriate', 'Inappropriate Content'),
        ('age_restricted', 'Age-Restricted Content (Underage)'),
        ('prohibited', 'Prohibited Item'),
        ('misleading', 'Misleading Description'),
        ('harassment', 'Harassment / Hate Speech'),
        ('spam', 'Spam / Fake Reviews'),
        ('other', 'Other'),
    ]

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='content_reports')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='seller_reports')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    description = models.TextField(help_text='Please describe the issue in detail')
    evidence_image = models.ImageField(upload_to='reports/', blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')
    resolution_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.product:
            target = self.product.product_name
        elif self.seller:
            target = self.seller.username
        else:
            target = 'Unknown'
        return f'{self.reporter.username} reported {target} - {self.get_reason_display()}'
