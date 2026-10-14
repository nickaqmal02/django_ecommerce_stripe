from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Storefront
    path('', views.product_list, name='product_list'),
    path('category/<int:category_id>/', views.product_list_by_category, name='product_list_by_category'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # Cart
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),

    # Checkout
    path('checkout/', views.checkout_form, name='checkout_form'),
    path('checkout/process/', views.process_checkout, name='process_checkout'),

    # Success
    path('success/<int:order_id>/', views.success_page, name='success'),

    # Track Order
    path('track/', views.track_order, name='track_order'),
    path('track/result/', views.track_result, name='track_result'),
    path('track/<str:order_id>/pdf/', views.order_pdf, name='order_pdf'),

    # Webhook
    path('webhook/', views.webhook, name='webhook'),
]
