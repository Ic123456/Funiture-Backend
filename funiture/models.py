from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings  
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from cloudinary.models import CloudinaryField
# Create your models here.

class InputEmail(models.Model):
    email = models.EmailField(unique=True, max_length=254)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Input Email"
        verbose_name_plural = "Input Emails"

    def __str__(self) -> str:
        # human-friendly representation
        return self.email or ""

    def clean(self):
        """Normalize and validate before saving via full_clean() / forms."""
        if self.email:
            self.email = self.email.strip().lower()
        try:
            validate_email(self.email)
        except ValidationError:
            raise ValidationError({"email": "Enter a valid email address."})

    def save(self, *args, **kwargs):
        # keep saved email normalized even if someone bypasses a form
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    
    def __str__(self):
        return self.name
    
    
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        
        if not self.slug:
            self.slug = slugify(self.name)
            unique_slug = self.slug
            counter = 1
            
            if Product.objects.filter(slug= unique_slug).exists():
                unique_slug = f'{self.slug}-{counter}'
                counter +=1 
                self.slug = unique_slug
        
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
    
    
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    slug = models.SlugField(unique=True, blank=True)
    image = CloudinaryField('image')
    featured = models.BooleanField(default=False)
    categories = models.ManyToManyField(Category, related_name='products', blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_popular = models.BooleanField(default=False)
    fabric = models.CharField(max_length=100, blank=True, null=True)
    dimension = models.CharField(max_length=100, blank=True, null=True)
    care = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return self.name
    
    
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        
        if not self.slug:
            self.slug = slugify(self.name)
            unique_slug = self.slug
            counter = 1
            
            if Product.objects.filter(slug= unique_slug).exists():
                unique_slug = f'{self.slug}-{counter}'
                counter +=1 
                self.slug = unique_slug
        
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
 
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery")
    image = image = CloudinaryField('image')
    
class Cart(models.Model):
    cart_code = models.CharField(max_length=11, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.cart_code
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cartitems")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="item")
    quantity = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in cart {self.cart.cart_code}"
    
    
class WishList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlists")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlists")
    created = models.DateTimeField(auto_now_add=True)
     
    class Meta:
        unique_together = ["user", "product"]
        
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
    
    
    
class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="address")
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    phone_number = PhoneNumberField()
    additional_phone_number = PhoneNumberField(blank=True, null=True)
    delivery_address = models.CharField(max_length=50)
    additional_information = models.CharField(max_length=255, blank=True, null=True)

    region = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    
class RecentlyViewed(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recently_viewed")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="viewed_by_users")
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user} viewed {self.product}"

class Order(models.Model):
    paystack_checkout_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    customer_email = models.EmailField()
    status = models.CharField(max_length=20, choices=[("Pending", "Pending"), ("Paid", "Paid")])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.paystack_checkout_id} - {self.status}"
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"Order {self.product.name} - {self.order.paystack_checkout_id}"
