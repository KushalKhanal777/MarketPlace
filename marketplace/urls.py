from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('products/', include("products.urls")),
    path('cart/', include("cart.urls")),
    path('blog/', include("blog.urls")),
    path('pages/', include("pages.urls")),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),

    # User Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/profile/', views.dashboard_profile, name='dashboard_profile'),
    path('dashboard/orders/', views.dashboard_orders, name='dashboard_orders'),
    path('dashboard/wishlist/', views.dashboard_wishlist, name='dashboard_wishlist'),
    path('dashboard/reviews/', views.dashboard_reviews, name='dashboard_reviews'),
    path('dashboard/settings/', views.dashboard_settings, name='dashboard_settings'),
    path('dashboard/earnings/', views.dashboard_earnings, name='dashboard_earnings'),
    path('dashboard/payment-settings/', views.dashboard_payment_settings, name='dashboard_payment_settings'),

    # Search
    path('search/', views.search_view, name='search'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),

    # Wishlist API
    path('api/wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),

    # Newsletter
    path('subscribe/', views.subscribe_view, name='subscribe'),

    # About & Contact
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),

    # Seller
    path('become-seller/', views.become_seller, name='become_seller'),
    path('seller/application-status/', views.seller_application_status, name='seller_application_status'),

    # Age Verification
    path('age-verify/', views.age_verify, name='age_verify'),

    # Content Reporting
    path('report/', views.report_content, name='report_content'),

    # Legal Pages
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('seller-guidelines/', views.seller_guidelines, name='seller_guidelines'),
    path('prohibited-items/', views.prohibited_items, name='prohibited_items'),
    path('content-policy/', views.content_policy, name='content_policy'),

    # Checkout
    path('checkout/', views.checkout_view, name='checkout'),
    path('order/<int:order_id>/confirmation/', views.order_confirmation_view, name='order_confirmation'),

    # Payment - eSewa
    path('payment/esewa/<int:order_id>/', views.esewa_payment_view, name='esewa_payment'),
    path('payment/esewa/verify/<int:order_id>/', views.esewa_verify_view, name='esewa_verify'),
    path('payment/esewa/fail/<int:order_id>/', views.esewa_fail_view, name='esewa_fail'),

    # Payment - Khalti
    path('api/payment/khalti/initiate/', views.khalti_initiate_view, name='khalti_initiate'),
    path('payment/khalti/<int:order_id>/', views.khalti_payment_view, name='khalti_payment'),
    path('payment/khalti/<int:order_id>/verify/', views.khalti_verify_view, name='khalti_verify'),
    path('payment/khalti/<int:order_id>/failure/', views.khalti_failure_view, name='khalti_failure'),
    path('payment/khalti/<int:order_id>/cancel/', views.khalti_cancel_view, name='khalti_cancel'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
