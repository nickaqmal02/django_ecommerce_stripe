from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Category, Product, ProductImage, Order, OrderItem, HomepageImage


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'product_count', 'created_at')
    search_fields = ('name',)

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(HomepageImage)
class HomepageImageAdmin(ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    list_editable = ('order', 'is_active')
    search_fields = ('title',)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price_at_purchase', 'line_total_display')

    def line_total_display(self, obj):
        return f"RM {(obj.price_at_purchase * obj.quantity) / 100:.2f}"
    line_total_display.short_description = 'Line Total'


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'category', 'price_display', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name',)
    inlines = [ProductImageInline]

    def price_display(self, obj):
        return f"RM {obj.price / 100:.2f}"
    price_display.short_description = 'Price'


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('order_id', 'name', 'total_display', 'paid', 'courier', 'tracking_number', 'created_at')
    list_filter = ('paid', 'courier', 'created_at')
    search_fields = ('order_id', 'name', 'email', 'tracking_number')
    list_editable = ('courier', 'tracking_number')
    inlines = [OrderItemInline]
    readonly_fields = ('order_id', 'stripe_session_id', 'total_display')

    def total_display(self, obj):
        return obj.total_display()
    total_display.short_description = 'Total'


admin.site.register(OrderItem)
