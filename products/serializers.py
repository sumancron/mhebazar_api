from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category, Subcategory, Product, ProductImage, Cart, Wishlist, 
    Quote, Rental, Review, ReviewMedia
)

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class SubcategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Subcategory
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'
        read_only_fields = ['created_at']

class ProductListSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_company = serializers.CharField(source='vendor.vendor_profile.company_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    main_image = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        exclude = ['vendor', 'category', 'subcategory']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_main_image(self, obj):
        return obj.get_main_image_url()
    
    def get_average_rating(self, obj):
        return obj.get_average_rating()
    
    def get_review_count(self, obj):
        return obj.get_review_count()

class ProductDetailSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_company = serializers.CharField(source='vendor.vendor_profile.company_name', read_only=True)
    vendor_email = serializers.CharField(source='vendor.email', read_only=True)
    vendor_phone = serializers.CharField(source='vendor.phone', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_average_rating(self, obj):
        return obj.get_average_rating()
    
    def get_review_count(self, obj):
        return obj.get_review_count()

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, required=False)
    
    class Meta:
        model = Product
        exclude = ['vendor', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('is_rental_available') and not data.get('rental_price_per_day'):
            raise serializers.ValidationError(
                "Rental price per day is required when rental is available."
            )
        return data
    
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        vendor = self.context['request'].user
        
        if not vendor.is_vendor:
            raise serializers.ValidationError("Only vendors can create products.")
        
        product = Product.objects.create(vendor=vendor, **validated_data)
        
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
        
        return product
    
    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if images_data:
            instance.images.all().delete()
            for image_data in images_data:
                ProductImage.objects.create(product=instance, **image_data)
        
        return instance

class CartSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_image = serializers.SerializerMethodField()
    vendor_name = serializers.CharField(source='product.vendor.name', read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'user']
    
    def get_product_image(self, obj):
        return obj.product.get_main_image_url()
    
    def get_total_price(self, obj):
        return obj.product.price * obj.quantity

class WishlistSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_image = serializers.SerializerMethodField()
    vendor_name = serializers.CharField(source='product.vendor.name', read_only=True)
    
    class Meta:
        model = Wishlist
        fields = '__all__'
        read_only_fields = ['created_at', 'user']
    
    def get_product_image(self, obj):
        return obj.product.get_main_image_url()

class QuoteSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    vendor_name = serializers.CharField(source='product.vendor.name', read_only=True)
    
    class Meta:
        model = Quote
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'user']

class QuoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = ['product', 'quantity', 'message', 'requirements', 'expected_delivery_date']
    
    def create(self, validated_data):
        user = self.context['request'].user
        return Quote.objects.create(user=user, **validated_data)

class RentalSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    vendor_name = serializers.CharField(source='product.vendor.name', read_only=True)
    
    class Meta:
        model = Rental
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'user', 'total_days', 'total_price']

class RentalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = ['product', 'start_date', 'end_date', 'notes', 'delivery_address', 'pickup_address', 'security_deposit']
    
    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        product = data.get('product')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise serializers.ValidationError("End date must be after start date.")
            
            if not product.is_rental_available:
                raise serializers.ValidationError("This product is not available for rental.")
            
            if not product.is_available_for_rental(start_date, end_date):
                raise serializers.ValidationError("Product is not available for the selected dates.")
            
            rental_days = (end_date - start_date).days + 1
            if rental_days < product.min_rental_days:
                raise serializers.ValidationError(
                    f"Minimum rental period is {product.min_rental_days} days."
                )
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        return Rental.objects.create(user=user, **validated_data)

class ReviewMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewMedia
        fields = '__all__'
        read_only_fields = ['created_at']

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    media = ReviewMediaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'user', 'is_verified_purchase', 'is_approved']

class ReviewCreateSerializer(serializers.ModelSerializer):
    media_files = serializers.ListField(
        child=serializers.FileField(), 
        write_only=True, 
        required=False
    )
    
    class Meta:
        model = Review
        fields = ['product', 'stars', 'title', 'message', 'media_files']
    
    def validate_stars(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Stars must be between 1 and 5.")
        return value
    
    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        user = self.context['request'].user
        
        if Review.objects.filter(user=user, product=validated_data['product']).exists():
            raise serializers.ValidationError("You have already reviewed this product.")
        
        review = Review.objects.create(user=user, **validated_data)
        
        for media_file in media_files:
            content_type = media_file.content_type
            file_type = 'image' if content_type.startswith('image/') else 'video'
            ReviewMedia.objects.create(
                review=review,
                file=media_file,
                file_type=file_type
            )
        
        return review

class VendorQuoteResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = ['status', 'vendor_response', 'quoted_price', 'expires_at']
    
    def validate(self, data):
        if data.get('status') == 'approved' and not data.get('quoted_price'):
            raise serializers.ValidationError("Quoted price is required when approving a quote.")
        return data

class VendorRentalResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = ['status', 'notes', 'security_deposit']