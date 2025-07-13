from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    
    # Subcategory URLs
    path('subcategories/', views.SubcategoryListView.as_view(), name='subcategory-list'),
    path('subcategories/<int:pk>/', views.SubcategoryDetailView.as_view(), name='subcategory-detail'),
    
    # Product URLs
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product-create'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product-update'),
    path('products/<int:pk>/delete/', views.ProductDestroyView.as_view(), name='product-delete'),
    
    # Vendor Product URLs
    path('vendor/products/', views.VendorProductListView.as_view(), name='vendor-product-list'),
    
    # Cart URLs
    path('cart/', views.CartListView.as_view(), name='cart-list'),
    path('cart/<int:pk>/', views.CartDetailView.as_view(), name='cart-detail'),
    
    # Wishlist URLs
    path('wishlist/', views.WishlistListView.as_view(), name='wishlist-list'),
    path('wishlist/<int:pk>/', views.WishlistDetailView.as_view(), name='wishlist-detail'),
    
    # Quote URLs
    path('quotes/', views.QuoteListView.as_view(), name='quote-list'),
    path('quotes/<int:pk>/', views.QuoteDetailView.as_view(), name='quote-detail'),
    
    # Vendor Quote URLs
    path('vendor/quotes/', views.VendorQuoteListView.as_view(), name='vendor-quote-list'),
    path('vendor/quotes/<int:pk>/update/', views.VendorQuoteUpdateView.as_view(), name='vendor-quote-update'),
    
    # Rental URLs
    path('rentals/', views.RentalListView.as_view(), name='rental-list'),
    path('rentals/<int:pk>/', views.RentalDetailView.as_view(), name='rental-detail'),
    
    # Vendor Rental URLs
    path('vendor/rentals/', views.VendorRentalListView.as_view(), name='vendor-rental-list'),
    path('vendor/rentals/<int:pk>/update/', views.VendorRentalUpdateView.as_view(), name='vendor-rental-update'),
    
    # Review URLs
    path('products/<int:product_id>/reviews/', views.ReviewListView.as_view(), name='review-list'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    
    # Utility URLs
    path('products/<int:product_id>/availability/', views.product_availability_check, name='product-availability'),
    path('products/<int:product_id>/stats/', views.product_stats, name='product-stats'),
    
    # Dashboard URLs
    path('vendor/dashboard/stats/', views.DashboardStatsView.as_view(), name='vendor-dashboard-stats'),
]