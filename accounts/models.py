# accounts/models.py

import os
import uuid
from django.db import models
from django.utils.deconstruct import deconstructible


@deconstructible
class UploadToUserPath:
    def __init__(self, folder):
        self.folder = folder

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = f"{self.folder}_{instance.id}_{uuid.uuid4().hex}.{ext}"
        return os.path.join("uploads", self.folder, str(instance.id), filename)


def user_upload_path(instance, filename):
    return UploadToUserPath("avatar")(instance, filename)


def vendor_logo_upload_path(instance, filename):
    return UploadToUserPath("vendor_logo")(instance, filename)


def vendor_banner_upload_path(instance, filename):
    return UploadToUserPath("vendor_banner")(instance, filename)


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True, max_length=254)
    name = models.CharField(max_length=250)
    password = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=32, null=True, blank=True)
    avatar = models.ImageField(upload_to=user_upload_path, null=True, blank=True)
    gender = models.CharField(max_length=250, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email


class VendorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    company_name = models.CharField(max_length=255)
    company_address = models.TextField()
    company_phone = models.CharField(max_length=32, null=True, blank=True)
    company_logo = models.ImageField(upload_to=vendor_logo_upload_path, null=True, blank=True)
    company_banner = models.ImageField(upload_to=vendor_banner_upload_path, null=True, blank=True)
    gst_number = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=70)
    organisation = models.CharField(max_length=100, null=True, blank=True)
    street1 = models.CharField(max_length=1024)
    street2 = models.CharField(max_length=1024, null=True, blank=True)
    city = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2)  # ISO Alpha-2 like IN, US
    phone = models.CharField(max_length=32)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.city})"
    

class ContactForm(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    company_name = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

