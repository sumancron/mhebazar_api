from rest_framework import serializers

from products.models import Product
from .models import Cart, Wishlist, Order, OrderItem, Delivery
from products.serializers import ProductListSerializer

class CartSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    
    class Meta:
        model = Cart
        fields = ['id', 'product', 'product_id', 'quantity', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'user']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_id', 'created_at']
        read_only_fields = ['created_at', 'user']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']
        read_only_fields = ['price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status = serializers.CharField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'total_amount', 'status', 'razorpay_order_id',
            'razorpay_payment_id', 'razorpay_signature', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'user', 'razorpay_order_id',
            'razorpay_payment_id', 'razorpay_signature'
        ]

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'order']

class CreateOrderSerializer(serializers.Serializer):
    cart_items = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Cart.objects.all(),
        required=True
    )
    shipping_address = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    pin_code = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    expected_delivery = serializers.DateField(required=True)

    def validate_cart_items(self, value):
        user = self.context['request'].user
        # Ensure all cart items belong to the current user
        for item in value:
            if item.user != user:
                raise serializers.ValidationError("Cart items must belong to the current user")
        return value

class RazorpayWebhookSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField(required=True)
    razorpay_payment_id = serializers.CharField(required=True)
    razorpay_signature = serializers.CharField(required=True)
    order_id = serializers.IntegerField(required=True)