from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Address, InputEmail, RecentlyViewed, Product, Category, CartItem, Cart, WishList, ProductImage, OrderItem, Order 

class  InputEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model =InputEmail
        fields = ["email"]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "first_name", "last_name", "email"]
        
class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]  
        
class ProductListSerializer(serializers.ModelSerializer):
    categories  = CategoryListSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ["id", "name", "description","price", "slug", "image", "featured", "categories", "stock",  "is_popular", "created_at"]

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["image"]
        
class ProductDetailSerializer(serializers.ModelSerializer):
    categories  = CategoryListSerializer(many=True, read_only=True)
    gallery = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ["id", "name", "description","price", "gallery", "fabric", "dimension",  "care", "categories"]

            
        
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only = True)
    sub_total = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "sub_total"]
        
    def get_sub_total(self, cartitems):
        total = cartitems.product.price * cartitems.quantity
        return total
    
class CartSerializer(serializers.ModelSerializer):
    cart_total = serializers.SerializerMethodField()
    cartitems = CartItemSerializer(read_only = True, many = True)
    class Meta:
        model = Cart
        fields = ["id", "cart_code", "cartitems", "cart_total"]
        
    def get_cart_total(self, cart):
        items = cart.cartitems.all()
        total = sum(( item.quantity * item.product.price for item in items ))
        return total
    
    
class WishListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only= True)
    product = ProductListSerializer(read_only= True)
    class Meta:
        model = WishList
        fields = ["id", "user", "product"]
        
     
        
class AddressSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only= True)
    class Meta:
        model = Address
        fields = ["id", "user", "first_name", "last_name", "phone_number", "additional_phone_number", "delivery_address", "additional_information", "region", "city"]
        
        
class RecentlyViewedSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only= True)
    product = ProductListSerializer(read_only= True)
    class Meta:
        model = RecentlyViewed
        fields = ["id", "user", "product"]
        
 
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "paystack_checkout_id", "amount", "currency", "customer_email", "status", "created_at"]
               
    
class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only= True)
    product = ProductListSerializer(read_only= True)
    class Meta:
        model = OrderItem
        fields = ["id", "order", "product", "quantity"]
