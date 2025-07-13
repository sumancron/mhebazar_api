from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'carts', views.CartViewSet, basename='cart')
router.register(r'wishlists', views.WishlistViewSet, basename='wishlist')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'deliveries', views.DeliveryViewSet, basename='delivery')

urlpatterns = [
    path('', include(router.urls)),
    path('razorpay/webhook/', views.RazorpayWebhookView.as_view({'post': 'create'}), name='razorpay-webhook'),
]