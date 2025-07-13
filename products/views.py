from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
import logging

from .models import (
    Category, Subcategory, Product, ProductImage, Cart, Wishlist, 
    Quote, Rental, Review, ReviewMedia
)
from .serializers import (
    CategorySerializer, SubcategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ProductCreateUpdateSerializer, CartSerializer,
    WishlistSerializer, QuoteSerializer, QuoteCreateSerializer,
    RentalSerializer, RentalCreateSerializer, ReviewSerializer,
    ReviewCreateSerializer, VendorQuoteResponseSerializer,
    VendorRentalResponseSerializer
)

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class IsVendor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_vendor

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsVendorOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.vendor == request.user

class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

class SubcategoryListView(generics.ListCreateAPIView):
    serializer_class = SubcategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Subcategory.objects.all()
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

class SubcategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer
    permission_classes = [IsAuthenticated]

class ProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'subcategory', 'type', 'selling_method', 'is_rental_available']
    search_fields = ['name', 'description', 'manufacturer', 'model']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related(
            'vendor', 'category', 'subcategory', 'vendor__vendor_profile'
        ).prefetch_related('images')
        
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        vendor_id = self.request.query_params.get('vendor')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
        
        return queryset

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'vendor', 'category', 'subcategory', 'vendor__vendor_profile'
        ).prefetch_related('images', 'reviews')

class ProductCreateView(generics.CreateAPIView):
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [IsAuthenticated, IsVendor]
    
    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user)

class ProductUpdateView(generics.UpdateAPIView):
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [IsAuthenticated, IsVendor, IsVendorOwner]
    
    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user)

class ProductDestroyView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsVendor, IsVendorOwner]
    
    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user)

class VendorProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticated, IsVendor]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user).select_related(
            'category', 'subcategory'
        ).prefetch_related('images')

class CartListView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).select_related('product')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CartDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

class WishlistListView(generics.ListCreateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WishlistDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

class QuoteListView(generics.ListCreateAPIView):
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Quote.objects.filter(user=self.request.user).select_related('product')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuoteCreateSerializer
        return QuoteSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class QuoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Quote.objects.filter(user=self.request.user)

class VendorQuoteListView(generics.ListAPIView):
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated, IsVendor]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return Quote.objects.filter(product__vendor=self.request.user).select_related(
            'user', 'product'
        )

class VendorQuoteUpdateView(generics.UpdateAPIView):
    serializer_class = VendorQuoteResponseSerializer
    permission_classes = [IsAuthenticated, IsVendor]
    
    def get_queryset(self):
        return Quote.objects.filter(product__vendor=self.request.user)

class RentalListView(generics.ListCreateAPIView):
    serializer_class = RentalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Rental.objects.filter(user=self.request.user).select_related('product')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RentalCreateSerializer
        return RentalSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RentalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RentalSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Rental.objects.filter(user=self.request.user)

class VendorRentalListView(generics.ListAPIView):
    serializer_class = RentalSerializer
    permission_classes = [IsAuthenticated, IsVendor]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return Rental.objects.filter(product__vendor=self.request.user).select_related(
            'user', 'product'
        )

class VendorRentalUpdateView(generics.UpdateAPIView):
    serializer_class = VendorRentalResponseSerializer
    permission_classes = [IsAuthenticated, IsVendor]
    
    def get_queryset(self):
        return Rental.objects.filter(product__vendor=self.request.user)

class ReviewListView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return Review.objects.filter(
            product_id=product_id, 
            is_approved=True
        ).select_related('user').prefetch_related('media')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReviewCreateSerializer
        return ReviewSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def product_availability_check(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not start_date or not end_date:
        return Response(
            {"error": "start_date and end_date are required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from datetime import datetime
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {"error": "Invalid date format. Use YYYY-MM-DD"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    is_available = product.is_available_for_rental(start_date, end_date)
    rental_price = product.calculate_rental_price(start_date, end_date) if is_available else 0
    
    return Response({
        "available": is_available,
        "rental_price": rental_price,
        "days": (end_date - start_date).days + 1
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def product_stats(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    stats = {
        "average_rating": product.get_average_rating(),
        "review_count": product.get_review_count(),
        "rating_distribution": {}
    }
    
    for i in range(1, 6):
        count = product.reviews.filter(stars=i, is_approved=True).count()
        stats["rating_distribution"][str(i)] = count
    
    return Response(stats)

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]
    
    def get(self, request):
        vendor = request.user
        
        total_products = Product.objects.filter(vendor=vendor).count()
        active_products = Product.objects.filter(vendor=vendor, is_active=True).count()
        
        total_quotes = Quote.objects.filter(product__vendor=vendor).count()
        pending_quotes = Quote.objects.filter(product__vendor=vendor, status='pending').count()
        
        total_rentals = Rental.objects.filter(product__vendor=vendor).count()
        active_rentals = Rental.objects.filter(product__vendor=vendor, status='active').count()
        
        total_reviews = Review.objects.filter(product__vendor=vendor).count()
        average_rating = Review.objects.filter(product__vendor=vendor).aggregate(
            avg_rating=Avg('stars')
        )['avg_rating'] or 0
        
        return Response({
            "products": {
                "total": total_products,
                "active": active_products,
                "inactive": total_products - active_products
            },
            "quotes": {
                "total": total_quotes,
                "pending": pending_quotes
            },
            "rentals": {
                "total": total_rentals,
                "active": active_rentals
            },
            "reviews": {
                "total": total_reviews,
                "average_rating": round(average_rating, 1)
            }
        })