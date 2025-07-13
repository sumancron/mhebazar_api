import os
import uuid
import logging
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

def category_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"category_{instance.id}_{uuid.uuid4().hex}.{ext}"
    return os.path.join("uploads", "categories", str(instance.id), filename)

def subcategory_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"subcategory_{instance.id}_{uuid.uuid4().hex}.{ext}"
    return os.path.join("uploads", "subcategories", str(instance.id), filename)

def product_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"product_image_{instance.product.id}_{uuid.uuid4().hex}.{ext}"
    return os.path.join("uploads", "products", str(instance.product.id), "images", filename)

def product_brochure_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"brochure_{instance.id}_{uuid.uuid4().hex}.{ext}"
    return os.path.join("uploads", "products", str(instance.id), "brochures", filename)

def review_media_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"review_media_{instance.review.id}_{uuid.uuid4().hex}.{ext}"
    return os.path.join("uploads", "reviews", str(instance.review.id), filename)

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    cat_image = models.ImageField(upload_to=category_image_upload_path, blank=True, null=True)
    cat_banner = models.ImageField(upload_to=category_image_upload_path, blank=True, null=True)
    product_details = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'is_active'])
        ]

    def __str__(self):
        return self.name

class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    sub_image = models.ImageField(upload_to=subcategory_image_upload_path, blank=True, null=True)
    sub_banner = models.ImageField(upload_to=subcategory_image_upload_path, blank=True, null=True)
    product_details = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Subcategories"
        unique_together = ('category', 'slug')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'is_active'])
        ]

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Product(models.Model):
    TYPE_CHOICES = (
        ('new', 'New'),
        ('used', 'Used'),
        ('rental', 'Rental'),
    )

    SELLING_METHOD_CHOICES = (
        ('direct', 'Direct Sale'),
        ('quote', 'Quote Request'),
        ('both', 'Both'),
    )

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='products'
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    manufacturer = models.CharField(max_length=255, blank=True, null=True)
    model = models.CharField(max_length=255, blank=True, null=True)
    product_details = models.JSONField(blank=True, null=True)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    brochure = models.FileField(upload_to=product_brochure_upload_path, blank=True, null=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='new')
    selling_method = models.CharField(max_length=10, choices=SELLING_METHOD_CHOICES, default='quote')
    is_active = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    min_order_quantity = models.PositiveIntegerField(default=1)
    is_rental_available = models.BooleanField(default=False)
    rental_price_per_day = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    min_rental_days = models.PositiveIntegerField(default=1)
    online_payment_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['model']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['category']),
            models.Index(fields=['subcategory']),
            models.Index(fields=['type']),
            models.Index(fields=['selling_method']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_rental_available']),
            models.Index(fields=['price']),
            models.Index(fields=['created_at']),
            models.Index(fields=['vendor']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.manufacturer or 'Unknown'} - {self.model or 'N/A'})"
        
    def get_main_image_url(self):
        main_image = self.images.first()
        return main_image.image.url if main_image else None
        
    def get_average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews:
            total_stars = sum(review.stars for review in reviews)
            return round(total_stars / len(reviews), 1)
        return None
        
    def get_review_count(self):
        return self.reviews.filter(is_approved=True).count()
        
    def is_available_for_rental(self, start_date, end_date):
        if not self.is_rental_available:
            return False
            
        conflicting_rentals = self.rentals.filter(
            status__in=['approved', 'active'],
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        return not conflicting_rentals.exists()
        
    def calculate_rental_price(self, start_date, end_date):
        if not self.rental_price_per_day:
            return Decimal('0.00')
        days = (end_date - start_date).days + 1
        return self.rental_price_per_day * days
        
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"New product created: {self.name} by vendor {self.vendor.id}")
        else:
            logger.info(f"Product updated: {self.name}")

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=product_image_upload_path)
    is_main = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_main', 'created_at']

    def __str__(self):
        return f"Image for {self.product.name}"

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.email} - {self.product.name} ({self.quantity})"

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.email} - {self.product.name}"

class Quote(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quotes')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='quotes')
    quantity = models.PositiveIntegerField(default=1)
    message = models.TextField()
    requirements = models.TextField(blank=True, null=True)
    expected_delivery_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    vendor_response = models.TextField(blank=True, null=True)
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Quote for {self.product.name} by {self.user.email}"

class Rental(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rentals')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='rentals')
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    delivery_address = models.TextField()
    pickup_address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Rental: {self.product.name} by {self.user.email}"

    def save(self, *args, **kwargs):
        if self.start_date and self.end_date:
            self.total_days = (self.end_date - self.start_date).days + 1
            if self.product.rental_price_per_day:
                self.total_price = self.product.rental_price_per_day * self.total_days
        super().save(*args, **kwargs)

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    stars = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.email} - {self.stars} stars"

class ReviewMedia(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to=review_media_upload_path)
    file_type = models.CharField(max_length=10, choices=[('image', 'Image'), ('video', 'Video')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Media for review {self.review.id}"