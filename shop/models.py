from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

# Product Categories
CATEGORY_CHOICES = [
    ('FOOD', 'Dog Food'),
    ('TOYS', 'Toys'),
    ('ACCESSORIES', 'Accessories'),
    ('HEALTH', 'Health & Wellness'),
    ('GROOMING', 'Grooming'),
    ('TRAINING', 'Training'),
    ('BEDDING', 'Bedding'),
    ('TRAVEL', 'Travel'),
    ('SAFETY', 'Safety'),
    ('OTHER', 'Other'),
]

# Order Status
ORDER_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('CONFIRMED', 'Confirmed'),
    ('PROCESSING', 'Processing'),
    ('SHIPPED', 'Shipped'),
    ('DELIVERED', 'Delivered'),
    ('CANCELLED', 'Cancelled'),
    ('REFUNDED', 'Refunded'),
]

# Payment Status
PAYMENT_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('PAID', 'Paid'),
    ('FAILED', 'Failed'),
    ('REFUNDED', 'Refunded'),
]

# UK Counties/Regions
UK_COUNTIES = [
    ('ENGLAND', 'England'),
    ('SCOTLAND', 'Scotland'),
    ('WALES', 'Wales'),
    ('NORTHERN_IRELAND', 'Northern Ireland'),
]


class Product(models.Model):
    """Product model with integrated category and images"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    brand = models.CharField(max_length=100, blank=True, null=True, help_text="Product brand name")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    compare_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Original price for comparison (shows as strikethrough)"
    )
    sku = models.CharField(max_length=100, unique=True, help_text="Stock Keeping Unit")
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5, help_text="Alert when stock falls below this")
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    dimensions = models.CharField(max_length=100, blank=True, null=True, help_text="L x W x H in cm")
    
    # Image fields
    primary_image = models.ImageField(upload_to='shop/products/', blank=True, null=True, help_text="Main product image")
    image_2 = models.ImageField(upload_to='shop/products/', blank=True, null=True, help_text="Secondary product image")
    image_3 = models.ImageField(upload_to='shop/products/', blank=True, null=True, help_text="Third product image")
    image_4 = models.ImageField(upload_to='shop/products/', blank=True, null=True, help_text="Fourth product image")
    
    is_active = models.BooleanField(default=True)
    is_bestseller = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True, null=True, help_text="Comma-separated tags")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.sku}"

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def discount_percentage(self):
        if self.compare_price and self.compare_price > self.price:
            return round(((self.compare_price - self.price) / self.compare_price) * 100, 1)
        return 0


    @property
    def images(self):
        """Return list of all non-empty images"""
        images = []
        if self.primary_image:
            images.append({
                'image': self.primary_image.url,
                'is_primary': True,
                'order': 0
            })
        if self.image_2:
            images.append({
                'image': self.image_2.url,
                'is_primary': False,
                'order': 1
            })
        if self.image_3:
            images.append({
                'image': self.image_3.url,
                'is_primary': False,
                'order': 2
            })
        if self.image_4:
            images.append({
                'image': self.image_4.url,
                'is_primary': False,
                'order': 3
            })
        return images


class Order(models.Model):
    """Order model"""
    order_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, help_text="Session key for anonymous users")
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Shipping Information
    shipping_first_name = models.CharField(max_length=100)
    shipping_last_name = models.CharField(max_length=100)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_county = models.CharField(max_length=50, choices=UK_COUNTIES, default='ENGLAND')
    shipping_postal_code = models.CharField(max_length=10, help_text="UK postcode (e.g., SW1A 1AA)")
    shipping_country = models.CharField(max_length=100, default='United Kingdom')
    shipping_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Billing Information (can be same as shipping)
    billing_first_name = models.CharField(max_length=100)
    billing_last_name = models.CharField(max_length=100)
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=100)
    billing_county = models.CharField(max_length=50, choices=UK_COUNTIES, default='ENGLAND')
    billing_postal_code = models.CharField(max_length=10, help_text="UK postcode (e.g., SW1A 1AA)")
    billing_country = models.CharField(max_length=100, default='United Kingdom')
    
    # Additional fields
    notes = models.TextField(blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

    def __str__(self):
        if self.user:
            return f"Order {self.order_number} - {self.user.name}"
        else:
            return f"Order {self.order_number} - Anonymous ({self.session_key[:8]}...)"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Order item model"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at time of purchase")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in Order {self.order.order_number}"

    @property
    def total_price(self):
        if self.price is None or self.quantity is None:
            return 0
        return self.price * self.quantity



