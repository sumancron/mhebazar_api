from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    LoginView,
)

from .crud.crud_views import (
    UserViewSet,
    VendorProfileViewSet,
    AddressViewSet,
    ContactFormViewSet,
    NewsletterSubscriberViewSet,
)

# ViewSet ke liye router
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'vendor-profiles', VendorProfileViewSet)
router.register(r'addresses', AddressViewSet)
router.register(r'contact-forms', ContactFormViewSet)
router.register(r'newsletter', NewsletterSubscriberViewSet)


urlpatterns = [
    # Manual views
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

    # Auto routes from viewsets
    path('', include(router.urls)),
]
