from django.contrib import admin
from django.utils.html import format_html, mark_safe

from .models import Category, Product, Brand, Review, Cart, CartItem, Wishlist, Order, OrderItem, Coupon, Subscriber, ProductImage, SellerProfile, Payout, SellerApplication, ContentReport


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'icon', 'product_count', 'is_active', 'created_at')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'description')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)
    ordering = ('name',)

    def product_count(self, obj):
        return obj.product_set.filter(status=True).count()
    product_count.short_description = 'Products'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'is_active')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'sort_order', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:60px;max-width:60px;border-radius:6px;object-fit:cover;" />',
                obj.image.url,
            )
        return '—'
    image_preview.short_description = 'Preview'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_name', 'category', 'brand', 'price', 'discount_price', 'stock', 'status', 'is_featured', 'is_bestseller', 'image_preview')
    list_display_links = ('id', 'product_name')
    search_fields = ('product_name', 'product_description')
    list_filter = ('category', 'brand', 'status', 'is_featured', 'is_bestseller', 'is_new_arrival', 'is_flash_sale')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'view_count', 'sold_count', 'image_preview')
    list_editable = ('status', 'is_featured', 'is_bestseller')
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductImageInline]

    fieldsets = (
        ('Product Information', {
            'fields': ('product_name', 'slug', 'product_description', 'category', 'brand')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'discount_price', 'stock', 'quantity')
        }),
        ('Flags', {
            'fields': ('status', 'is_featured', 'is_bestseller', 'is_new_arrival', 'is_flash_sale', 'flash_sale_end'),
        }),
        ('Media', {
            'fields': ('product_image', 'image_preview'),
            'description': 'Upload a main product image. Additional images can be added below.',
        }),
        ('Statistics', {
            'fields': ('sold_count', 'view_count'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def image_preview(self, obj):
        if obj.product_image:
            return format_html(
                '<img src="{}" style="max-height:80px;max-width:80px;border-radius:8px;object-fit:cover;" />',
                obj.product_image.url,
            )
        return mark_safe(
            '<div style="width:80px;height:80px;background:#f5f3f0;border-radius:8px;'
            'display:flex;align-items:center;justify-content:center;color:#78716c;font-size:12px;">'
            'No Image</div>'
        )
    image_preview.short_description = 'Preview'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'alt_text', 'sort_order', 'image_preview')
    list_filter = ('product',)
    list_editable = ('sort_order',)
    ordering = ('sort_order',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:60px;max-width:60px;border-radius:6px;object-fit:cover;" />',
                obj.image.url,
            )
        return '—'
    image_preview.short_description = 'Preview'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'rating', 'title', 'helpful_count', 'created_at')
    list_display_links = ('id', 'title')
    search_fields = ('title', 'comment', 'user__username', 'product__product_name')
    list_filter = ('rating', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'coupon', 'total_items', 'total_price', 'created_at')
    list_filter = ('coupon',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'subtotal')
    readonly_fields = ('created_at',)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_number', 'user', 'full_name', 'status', 'total_amount', 'payment_method', 'payment_status', 'created_at')
    list_display_links = ('id', 'order_number')
    search_fields = ('order_number', 'user__username', 'email', 'full_name')
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at')
    list_editable = ('status', 'payment_status')
    readonly_fields = ('created_at', 'updated_at', 'transaction_id')
    ordering = ('-created_at',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'price', 'quantity', 'subtotal')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'discount_amount', 'discount_percent', 'min_purchase', 'used_count', 'max_uses', 'is_active', 'valid_from', 'valid_to')
    list_display_links = ('id', 'code')
    search_fields = ('code',)
    list_filter = ('is_active', 'valid_from', 'valid_to')
    list_editable = ('is_active',)
    ordering = ('-created_at',)


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'is_active', 'created_at')
    list_display_links = ('id', 'email')
    search_fields = ('email',)
    list_filter = ('is_active',)
    list_editable = ('is_active',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'esewa_number', 'khalti_number', 'preferred_method', 'is_verified', 'total_earnings_display', 'pending_balance_display')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'user__email', 'esewa_number', 'khalti_number')
    list_filter = ('preferred_method', 'is_verified')
    list_editable = ('is_verified',)
    readonly_fields = ('created_at',)

    def total_earnings_display(self, obj):
        return f'Rs. {obj.total_earnings:,.2f}'
    total_earnings_display.short_description = 'Total Earnings'

    def pending_balance_display(self, obj):
        return f'Rs. {obj.pending_balance:,.2f}'
    pending_balance_display.short_description = 'Pending Balance'


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'amount_display', 'method', 'account_number', 'status', 'reference_id', 'created_at', 'completed_at')
    list_display_links = ('id', 'seller')
    search_fields = ('seller__username', 'account_number', 'reference_id')
    list_filter = ('status', 'method', 'created_at')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'completed_at')
    ordering = ('-created_at',)

    def amount_display(self, obj):
        return f'Rs. {obj.amount:,.2f}'
    amount_display.short_description = 'Amount'

    def save_model(self, request, obj, form, change):
        if obj.status == 'completed' and not obj.completed_at:
            from django.utils import timezone
            obj.completed_at = timezone.now()
            obj.processed_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SellerApplication)
class SellerApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'business_type', 'status', 'is_age_verified', 'city', 'province', 'created_at')
    list_display_links = ('id', 'full_name')
    search_fields = ('full_name', 'email', 'phone', 'business_name', 'document_number')
    list_filter = ('status', 'business_type', 'is_age_verified', 'province', 'created_at')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'full_name', 'phone', 'email', 'date_of_birth', 'is_age_verified', 'address', 'city', 'province')
        }),
        ('Business Information', {
            'fields': ('business_type', 'business_name', 'business_reg_number', 'pan_number', 'business_description', 'product_categories', 'selling_reason', 'estimated_monthly_sales')
        }),
        ('KYC Documents', {
            'fields': ('document_type', 'document_number', 'document_front', 'document_back')
        }),
        ('Legal Agreements', {
            'fields': ('agreed_to_terms', 'agreed_to_privacy', 'agreed_to_seller_policy', 'consent_to_data_processing')
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'review_notes', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'product', 'seller', 'reason', 'is_resolved', 'created_at')
    list_display_links = ('id', 'reporter')
    search_fields = ('reporter__username', 'product__product_name', 'seller__username', 'description')
    list_filter = ('reason', 'is_resolved', 'created_at')
    list_editable = ('is_resolved',)
    readonly_fields = ('created_at', 'resolved_at')
    ordering = ('-created_at',)
