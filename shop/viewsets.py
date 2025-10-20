from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, F
from decimal import Decimal
import uuid

from .models import (
    Product, Order, OrderItem
)
from .serializers import (
    ProductSerializer, ProductListSerializer,
    OrderSerializer, OrderCreateSerializer, OrderItemSerializer
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for products"""
    queryset = Product.objects.filter(is_active=True)
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by featured products
        featured = self.request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_bestseller=True)
        
        # Filter by in stock
        in_stock = self.request.query_params.get('in_stock')
        if in_stock and in_stock.lower() == 'true':
            queryset = queryset.filter(stock_quantity__gt=0)
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(brand__icontains=search) |
                Q(tags__icontains=search) |
                Q(sku__icontains=search)
            )
        
        # Price range filter
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Ordering
        ordering = self.request.query_params.get('ordering')
        if ordering in ['price', '-price', 'name', '-name', 'created_at', '-created_at']:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """Get related products in the same category"""
        product = self.get_object()
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        serializer = ProductListSerializer(related_products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def bestseller(self, request):
        """Get bestseller products"""
        bestseller_products = self.get_queryset().filter(is_bestseller=True)
        
        page = self.paginate_queryset(bestseller_products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(bestseller_products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search endpoint"""
        search_term = request.query_params.get('q', '')
        if not search_term:
            return Response({'results': []})
        
        products = self.get_queryset().filter(
            Q(name__icontains=search_term) | 
            Q(description__icontains=search_term) |
            Q(brand__icontains=search_term) |
            Q(tags__icontains=search_term) |
            Q(sku__icontains=search_term)
        )
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get all available categories with product counts"""
        from .models import CATEGORY_CHOICES
        categories = []
        for choice in CATEGORY_CHOICES:
            category_code, category_name = choice
            product_count = Product.objects.filter(category=category_code, is_active=True).count()
            categories.append({
                'code': category_code,
                'name': category_name,
                'product_count': product_count
            })
        
        return Response(categories)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for orders"""
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]  # Allow anonymous users to create orders
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user)
        else:
            # For anonymous users, they can only view orders they created in this session
            session_key = self.request.session.session_key
            if session_key:
                return Order.objects.filter(session_key=session_key)
            return Order.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create order with items"""
        # Expect order data with items in the request
        order_data = request.data.copy()
        items_data = order_data.pop('items', [])
        
        if not items_data:
            return Response(
                {'error': 'Order must contain at least one item'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate items
        for item_data in items_data:
            product_id = item_data.get('product')
            quantity = item_data.get('quantity', 1)
            
            try:
                product = Product.objects.get(id=product_id, is_active=True)
                if not product.is_in_stock:
                    return Response(
                        {'error': f'Product {product.name} is out of stock'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if quantity > product.stock_quantity:
                    return Response(
                        {'error': f'Not enough stock for {product.name}. Available: {product.stock_quantity}'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Product.DoesNotExist:
                return Response(
                    {'error': f'Product with id {product_id} not found or inactive'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Calculate totals
        subtotal = Decimal('0.00')
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product'])
            quantity = item_data['quantity']
            subtotal += product.price * quantity
        
        tax_rate = Decimal('0.20')  # 20% VAT rate for UK
        tax_amount = subtotal * tax_rate
        shipping_cost = Decimal('4.99')  # Fixed UK shipping cost
        total_amount = subtotal + tax_amount + shipping_cost
        
        # Create order
        serializer = self.get_serializer(data=order_data)
        if serializer.is_valid():
            order_data = serializer.validated_data.copy()
            if request.user.is_authenticated:
                order_data.update({
                    'user': request.user,
                    'session_key': None,
                })
            else:
                session_key = request.session.session_key
                if not session_key:
                    request.session.save()
                    session_key = request.session.session_key
                order_data.update({
                    'user': None,
                    'session_key': session_key,
                })
            
            order_data.update({
                'subtotal': subtotal,
                'tax_amount': tax_amount,
                'shipping_cost': shipping_cost,
                'total_amount': total_amount,
                'status': 'PENDING',
                'payment_status': 'PENDING'
            })
            
            order = Order.objects.create(**order_data)
            
            # Create order items and update stock
            for item_data in items_data:
                product = Product.objects.get(id=item_data['product'])
                quantity = item_data['quantity']
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )
                
                # Update product stock
                product.stock_quantity = F('stock_quantity') - quantity
                product.save(update_fields=['stock_quantity'])
            
            # Return created order
            order_serializer = OrderSerializer(order, context={'request': request})
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

