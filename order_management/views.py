from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
import razorpay
from django.conf import settings
from django.shortcuts import get_object_or_404

from .models import Cart, OrderItem, Wishlist, Order, Delivery
from .serializers import (
    CartSerializer, WishlistSerializer, OrderSerializer,
    DeliverySerializer, CreateOrderSerializer, RazorpayWebhookSerializer
)
from products.models import Product

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).select_related('product')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def add_to_cart(self, request):
        wishlist_item = get_object_or_404(
            Wishlist,
            id=request.data.get('wishlist_id'),
            user=request.user
        )
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=wishlist_item.product,
            defaults={'quantity': 1}
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        wishlist_item.delete()
        return Response(status=status.HTTP_201_CREATED)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')
    
    def create(self, request):
        serializer = CreateOrderSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Calculate total amount
        total = 0
        cart_items = data['cart_items']
        for item in cart_items:
            total += item.product.price * item.quantity
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            status='PENDING'
        )
        
        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        
        # Create delivery
        Delivery.objects.create(
            order=order,
            shipping_address=data['shipping_address'],
            city=data['city'],
            state=data['state'],
            pin_code=data['pin_code'],
            phone=data['phone'],
            expected_delivery=data['expected_delivery']
        )
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ))
        
        # Create Razorpay order
        razorpay_order = client.order.create({
            'amount': int(total * 100),  # Amount in paise
            'currency': 'INR',
            'payment_capture': 1  # Auto capture payment
        })
        
        # Update order with Razorpay ID
        order.razorpay_order_id = razorpay_order['id']
        order.save()
        
        return Response({
            'order_id': order.id,
            'razorpay_order_id': razorpay_order['id'],
            'amount': total,
            'currency': 'INR',
            'key': settings.RAZORPAY_KEY_ID
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def retry_payment(self, request, pk=None):
        order = self.get_object()
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ))
        
        # Create new Razorpay order
        razorpay_order = client.order.create({
            'amount': int(order.total_amount * 100),  # Amount in paise
            'currency': 'INR',
            'payment_capture': 1  # Auto capture payment
        })
        
        # Update order with new Razorpay ID
        order.razorpay_order_id = razorpay_order['id']
        order.status = 'PENDING'
        order.save()
        
        return Response({
            'order_id': order.id,
            'razorpay_order_id': razorpay_order['id'],
            'amount': order.total_amount,
            'currency': 'INR',
            'key': settings.RAZORPAY_KEY_ID
        })
    
    @action(detail=False, methods=['post'])
    def from_wishlist(self, request):
        wishlist_item = get_object_or_404(
            Wishlist,
            id=request.data.get('wishlist_id'),
            user=request.user
        )
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=wishlist_item.product.price,
            status='PENDING'
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=wishlist_item.product,
            quantity=1,
            price=wishlist_item.product.price
        )
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ))
        
        # Create Razorpay order
        razorpay_order = client.order.create({
            'amount': int(wishlist_item.product.price * 100),  # Amount in paise
            'currency': 'INR',
            'payment_capture': 1  # Auto capture payment
        })
        
        # Update order with Razorpay ID
        order.razorpay_order_id = razorpay_order['id']
        order.save()
        
        # Delete wishlist item
        wishlist_item.delete()
        
        return Response({
            'order_id': order.id,
            'razorpay_order_id': razorpay_order['id'],
            'amount': wishlist_item.product.price,
            'currency': 'INR',
            'key': settings.RAZORPAY_KEY_ID
        }, status=status.HTTP_201_CREATED)

class DeliveryViewSet(viewsets.ModelViewSet):
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Delivery.objects.filter(order__user=self.request.user).select_related('order')
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()
    
    @action(detail=True, methods=['get'])
    def track(self, request, pk=None):
        delivery = self.get_object()
        return Response({
            'status': delivery.status,
            'expected_delivery': delivery.expected_delivery,
            'delivery_date': delivery.delivery_date
        })

class RazorpayWebhookView(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    
    def create(self, request):
        serializer = RazorpayWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Verify payment signature
        client = razorpay.Client(auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ))
        
        params = {
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        }
        
        try:
            client.utility.verify_payment_signature(params)
            
            # Update order status
            order = Order.objects.get(id=data['order_id'])
            order.status = 'PAID'
            order.razorpay_payment_id = data['razorpay_payment_id']
            order.razorpay_signature = data['razorpay_signature']
            order.save()
            
            # Clear cart items
            order.items.all().delete()
            
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Handle verification failure
            order = Order.objects.get(id=data['order_id'])
            order.status = 'FAILED'
            order.save()
            
            return Response(
                {'error': 'Signature verification failed'},
                status=status.HTTP_400_BAD_REQUEST
            )