from django.contrib import admin
from .models import Product,InputEmail,  Order, OrderItem,  RecentlyViewed, Address, Category, Cart, CartItem, WishList, ProductImage


# Register your models here.

class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "featured")
admin.site.register(Product, ProductAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
admin.site.register(Category, CategoryAdmin)

admin.site.register({Order, InputEmail, OrderItem, Cart, CartItem, WishList, ProductImage, Address, RecentlyViewed})

