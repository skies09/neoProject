from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    Product, Order, OrderItem
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'brand', 'sku', 'category', 'price', 'stock_quantity', 
        'is_active', 'is_bestseller', 'stock_status'
    ]
    list_filter = [
        'category', 'brand', 'is_active', 'is_bestseller', 
        'created_at', 'updated_at'
    ]
    search_fields = ['name', 'brand', 'sku', 'description', 'tags']
    readonly_fields = ['created_at', 'updated_at', 'discount_percentage']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'brand', 'category', 'sku', 'tags')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price', 'discount_percentage')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'low_stock_threshold', 'weight', 'dimensions')
        }),
        ('Images', {
            'fields': ('primary_image', 'image_2', 'image_3', 'image_4')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_bestseller')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def stock_status(self, obj):
        if obj.stock_quantity == 0:
            return format_html('<span style="color: red;">Out of Stock</span>')
        elif obj.is_low_stock:
            return format_html('<span style="color: orange;">Low Stock</span>')
        else:
            return format_html('<span style="color: green;">In Stock</span>')
    stock_status.short_description = 'Stock Status'


class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price_display', 'created_at']
    fields = ['product', 'quantity', 'price', 'total_price_display', 'created_at']
    verbose_name = "Order Item"
    verbose_name_plural = "Order Items"
    
    def total_price_display(self, obj):
        try:
            return f"£{obj.total_price:.2f}"
        except (TypeError, ValueError):
            return "£0.00"
    total_price_display.short_description = 'Total Price'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'session_key', 'status', 'payment_status', 
        'total_amount', 'items_summary', 'created_at'
    ]
    list_filter = [
        'status', 'payment_status', 'created_at', 'shipped_at'
    ]
    search_fields = [
        'order_number', 'user__name', 'user__email',
        'shipping_first_name', 'shipping_last_name'
    ]
    readonly_fields = [
        'order_number', 'session_key', 'created_at', 'updated_at', 'shipped_at', 'delivered_at'
    ]
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'session_key', 'status', 'payment_status', 'notes')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'total_amount')
        }),
        ('Shipping Information', {
            'fields': (
                'shipping_first_name', 'shipping_last_name', 'shipping_address',
                'shipping_city', 'shipping_county', 'shipping_postal_code',
                'shipping_country', 'shipping_phone', 'tracking_number'
            )
        }),
        ('Billing Information', {
            'fields': (
                'billing_first_name', 'billing_last_name', 'billing_address',
                'billing_city', 'billing_county', 'billing_postal_code',
                'billing_country'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    
    def items_summary(self, obj):
        """Display a summary of order items"""
        items = obj.items.all()
        if not items:
            return "No items"
        
        item_count = sum(item.quantity for item in items)
        if len(items) == 1:
            return f"{item_count} item"
        else:
            return f"{item_count} items ({len(items)} products)"
    items_summary.short_description = 'Items'
    
    def mark_as_shipped(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='SHIPPED', shipped_at=timezone.now())
        self.message_user(request, f'{updated} orders marked as shipped.')
    mark_as_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_as_delivered(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='DELIVERED', delivered_at=timezone.now())
        self.message_user(request, f'{updated} orders marked as delivered.')
    mark_as_delivered.short_description = "Mark selected orders as delivered"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='CANCELLED')
        self.message_user(request, f'{updated} orders marked as cancelled.')
    mark_as_cancelled.short_description = "Mark selected orders as cancelled"


# OrderItem is now only accessible through OrderAdmin inline
# No separate admin interface for OrderItem


# Customize admin site
admin.site.site_header = "NeoProject Shop Administration"
admin.site.site_title = "Shop Admin"
admin.site.index_title = "Welcome to Shop Administration"