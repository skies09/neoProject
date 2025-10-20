from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Product, Order, OrderItem
)

User = get_user_model()


class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    is_in_stock = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'brand', 'category',
            'price', 'compare_price', 'sku', 'stock_quantity', 
            'low_stock_threshold', 'weight', 'dimensions', 'is_active',
            'is_bestseller', 'tags', 'images',
            'primary_image', 'image_2', 'image_3', 'image_4',
            'is_in_stock', 'is_low_stock', 'discount_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_images(self, obj):
        return obj.images


class ProductListSerializer(serializers.ModelSerializer):
    """Simplified serializer for product lists"""
    primary_image_url = serializers.SerializerMethodField()
    is_in_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'brand', 'category', 'price', 'compare_price',
            'sku', 'is_in_stock', 'primary_image_url', 'discount_percentage',
            'is_bestseller', 'created_at'
        ]
    
    def get_primary_image_url(self, obj):
        if obj.primary_image:
            return obj.primary_image.url
        return None




class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 
            'quantity', 'price', 'total_price'
        ]
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'session_key', 'user_name', 'user_email',
            'status', 'payment_status', 'subtotal', 'tax_amount',
            'shipping_cost', 'total_amount',
            'shipping_first_name', 'shipping_last_name', 'shipping_address',
            'shipping_city', 'shipping_county', 'shipping_postal_code',
            'shipping_country', 'shipping_phone', 'billing_first_name',
            'billing_last_name', 'billing_address', 'billing_city',
            'billing_county', 'billing_postal_code', 'billing_country',
            'notes', 'tracking_number', 'shipped_at', 'delivered_at',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'user', 'session_key', 'created_at', 'updated_at',
            'shipped_at', 'delivered_at'
        ]
    
    def get_user_name(self, obj):
        return obj.user.name if obj.user else "Anonymous"
    
    def get_user_email(self, obj):
        return obj.user.email if obj.user else None


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders"""
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'shipping_first_name', 'shipping_last_name', 'shipping_address',
            'shipping_city', 'shipping_county', 'shipping_postal_code',
            'shipping_country', 'shipping_phone', 'billing_first_name',
            'billing_last_name', 'billing_address', 'billing_city',
            'billing_county', 'billing_postal_code', 'billing_country',
            'notes', 'items'
        ]
    
    def validate(self, attrs):
        # Validate required shipping fields
        required_shipping_fields = [
            'shipping_first_name', 'shipping_last_name', 'shipping_address',
            'shipping_city', 'shipping_county', 'shipping_postal_code'
        ]
        
        for field in required_shipping_fields:
            if not attrs.get(field):
                raise serializers.ValidationError(f"{field.replace('_', ' ').title()} is required.")
        
        # Validate required billing fields
        required_billing_fields = [
            'billing_first_name', 'billing_last_name', 'billing_address',
            'billing_city', 'billing_county', 'billing_postal_code'
        ]
        
        for field in required_billing_fields:
            if not attrs.get(field):
                raise serializers.ValidationError(f"{field.replace('_', ' ').title()} is required.")
        
        # Validate UK postcodes
        import re
        uk_postcode_pattern = r'^[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}$'
        
        shipping_postcode = attrs.get('shipping_postal_code', '').upper()
        if shipping_postcode and not re.match(uk_postcode_pattern, shipping_postcode):
            raise serializers.ValidationError("Invalid UK postcode format for shipping address.")
        
        billing_postcode = attrs.get('billing_postal_code', '').upper()
        if billing_postcode and not re.match(uk_postcode_pattern, billing_postcode):
            raise serializers.ValidationError("Invalid UK postcode format for billing address.")
        
        # Ensure country is UK
        if attrs.get('shipping_country') and attrs.get('shipping_country').lower() not in ['united kingdom', 'uk', 'great britain']:
            raise serializers.ValidationError("We only ship to the United Kingdom.")
        
        if attrs.get('billing_country') and attrs.get('billing_country').lower() not in ['united kingdom', 'uk', 'great britain']:
            raise serializers.ValidationError("We only accept billing addresses in the United Kingdom.")
        
        return attrs

