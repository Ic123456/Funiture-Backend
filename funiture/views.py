from .models import Order, OrderItem, Product, Category, Cart, CartItem, WishList, Address, RecentlyViewed
from .serializers import (ProductListSerializer, InputEmailSerializer, CategoryListSerializer, ProductDetailSerializer, 
                           CartItemSerializer, CartSerializer, RecentlyViewedSerializer,
                          WishListSerializer, UserSerializer, AddressSerializer, OrderItemSerializer
)
import uuid
from .paystack import checkout
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
import hmac
import hashlib
import json
from django.conf import settings

from rest_framework import status, permissions
from django.db import transaction
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
# Create your views here.

User = get_user_model()


class InputEmailCreateView(APIView):
    def post(self, request):
        serializer = InputEmailSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Email saved successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class RecentlyViewedApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        recent_items = RecentlyViewed.objects.filter(user=user).order_by('-viewed_at')[:10]
        serializer = RecentlyViewedSerializer(recent_items, many=True)
        return Response(serializer.data, status=200)
    
    def post(self, request):
        product_id = request.data.get("product_id")
        
        # 1. Get user
        try:
            user = request.user
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # 2. Get product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        try:
            with transaction.atomic():

                # 3. Create or update entry
                RecentlyViewed.objects.update_or_create(
                    user=user,
                    product=product,
                    defaults={"viewed_at": timezone.now()}
                )

                # 4. Enforce max 10 items
                recent_items = (
                    RecentlyViewed.objects
                    .filter(user=user)
                    .order_by('-viewed_at')
                )

                # get items AFTER the first 10
                items_to_delete = recent_items[10:].values_list('id', flat=True)

                if items_to_delete:
                    RecentlyViewed.objects.filter(id__in=items_to_delete).delete()

        except Exception as e:
            raise e

        return Response({"message": "Product added to recently viewed"}, status=201)

class Profileview(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        
        serializer = UserSerializer(user)
        return Response(serializer.data)


class ProductListAPIView(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    

class ProductList(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer
    queryset = Product.objects.all()

class GetProductListAPIView(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer

    def post(self, request):
            ids = request.data.get('ids', [])
            # validate & convert safely
            try:
                ids = [int(i) for i in ids]
            except Exception:
                return Response({"detail": "ids must be a list of integers"}, status=400)

            products = Product.objects.filter(id__in=ids)
            serializer = ProductListSerializer(products, many=True)
            return Response(serializer.data)
        
        

class CategoryListAPIView(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer
    
    
class ProductDetailView(generics.RetrieveAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"
    

class CartView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        cart_code = request.COOKIES.get("cart_code")

        # If no cart_code, create one
        if not cart_code:
            cart_code = str(uuid.uuid4())

        # Get or create cart
        cart, created = Cart.objects.get_or_create(
            cart_code=cart_code
        )

        serializer = CartSerializer(cart)

        response = Response(serializer.data, status=status.HTTP_200_OK)

        # Save cart_code in cookie (important)
        response.set_cookie(
            key="cart_code",
            value=cart_code,
            httponly=True,
            samesite="Lax"
        )

        return response


class AddToCart(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        product_id = request.data.get("product_id")
        
        if not product_id:
            return Response({"error": "Product ID is required"}, status=400)
        
        cart_code = request.COOKIES.get("cart_code")
        
        if not cart_code:
            cart_code = str(uuid.uuid4())
        
        cart, _ = Cart.objects.get_or_create(cart_code= cart_code)
        product = Product.objects.get(id= product_id)
        
        cartitem, created = CartItem.objects.get_or_create(cart= cart, product= product)
        cartitem.quantity = 1
        cartitem.save()
        
        
        
        serializer = CartSerializer(cart)
        response =  Response(serializer.data)
    
        response.set_cookie(
            key="cart_code",
            value=cart_code,
            httponly=True,
            secure=False,
        )
        return response
    
    
    
class CartDetailedView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    def put(self, request):
        cart_code = request.COOKIES.get("cart_code")
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")

        # 1️⃣ Resolve cart (never fail)
        if cart_code:
            cart, _ = Cart.objects.get_or_create(cart_code=cart_code)
        else:
            cart = Cart.objects.create(cart_code=str(uuid.uuid4()))
            cart_code = cart.cart_code

        # 2️⃣ Resolve product + cart item safely
        product = get_object_or_404(Product, id=product_id)
        cartitem, _ = CartItem.objects.get_or_create(cart=cart, product=product)

        # 3️⃣ Apply update
        cartitem.quantity = quantity
        cartitem.save()

        # 4️⃣ Build response
        response = Response({
            "data": CartItemSerializer(cartitem).data,
            "message": "Cart item updated successfully"
        })

        # 5️⃣ Attach cookie ONCE
        response.set_cookie(
            key="cart_code",
            value=cart_code,
            httponly=True,
            secure=False,
            samesite="Lax"
        )

        return response

    def delete(self, request):
        product_id = request.data.get("product_id")
        cart_code = request.COOKIES.get("cart_code")

        if not product_id:
            return Response(
                {"error": "Product ID required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # If no cart cookie → nothing to delete
        if not cart_code:
            return Response(status=status.HTTP_204_NO_CONTENT)

        # Try to get cart safely
        cart = Cart.objects.filter(cart_code=cart_code).first()
        if not cart:
            return Response(status=status.HTTP_204_NO_CONTENT)

        # Try to get cart item safely
        cart_item = CartItem.objects.filter(
            cart=cart,
            product_id=product_id
        ).first()

        if cart_item:
            cart_item.delete()

        # Always return 204 (idempotent)
        return Response(status=status.HTTP_204_NO_CONTENT)

        

class WishListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wishlist = WishList.objects.filter(user=request.user)
        serializer = WishListSerializer(wishlist, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class WishListDetailedView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        product_id = request.query_params.get("product_id")

        if not product_id:
            return Response(
                {"error": "Product ID required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        product = get_object_or_404(Product, id=product_id)
        wishlist = get_object_or_404(
            WishList,
            user=request.user,
            product=product
        )

        serializer = WishListSerializer(wishlist)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AddToWishListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        product_ids = request.data.get("product_id")
        user = request.user
        if not product_ids:
            return Response(
                {"error": "Product ID(s) required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure product_ids is always a list
        if isinstance(product_ids, int):
            product_ids = [product_ids]
        elif not isinstance(product_ids, list):
            return Response(
                {"error": "product_id must be a number or list of numbers"},
                status=status.HTTP_400_BAD_REQUEST
            )

        added = []
        removed = []

        for pid in product_ids:
            try:
                product = Product.objects.get(id=pid)
            except Product.DoesNotExist:
                continue  # skip invalid IDs

            wishlist_entry = WishList.objects.filter(user=user, product=product)

            if wishlist_entry.exists():
                wishlist_entry.delete()
                removed.append(pid)
            else:
                new_wishlist = WishList.objects.create(user=user, product=product)
                added.append(pid)

        return Response(
            {"added": added, "removed": removed},
            status=status.HTTP_200_OK
        )

class ProductSearchView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        query = request.query_params.get("query")
        if not query:
            return Response("No query provided", status=400)
        
        product = Product.objects.filter(Q(name__icontains=query ) | 
                                        Q(description__icontains=query) |
                                        Q(categories__name__icontains=query))
        
        serializer = ProductListSerializer(product, many=True)
        return Response(serializer.data)

class AddressView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        addrss = Address.objects.filter(user= user)
        serializer = AddressSerializer(addrss, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        phone_number = request.data.get("phone_number")
        additional_phone_number = request.data.get("additional_phone_number")
        delivery_address = request.data.get("delivery_address")
        additional_information = request.data.get("additional_information")
        region = request.data.get("region")
        city = request.data.get("city")
        
        
        user = request.user

        addrss = Address.objects.create(user=user, first_name=first_name, last_name=last_name, phone_number=phone_number, additional_phone_number=additional_phone_number, delivery_address=delivery_address, additional_information=additional_information, region=region, city=city)
        serializer = AddressSerializer(addrss)
        return Response(serializer.data)
    
    def put(self, request):
        address_id = request.data.get("address_id")
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        phone_number = request.data.get("phone_number")
        additional_phone_number = request.data.get("additional_phone_number")
        delivery_address = request.data.get("delivery_address")
        additional_information = request.data.get("additional_information")
        region = request.data.get("region")
        city = request.data.get("city")
        
        
        user = request.user
        
        
        addrss = Address.objects.get(user=user, id=address_id)
        addrss.first_name = first_name
        addrss.last_name = last_name
        addrss.phone_number = phone_number
        addrss.additional_phone_number = additional_phone_number
        addrss.delivery_address = delivery_address
        addrss.additional_information = additional_information
        addrss.region = region
        addrss.city = city
        addrss.save()
        
        serializer = AddressSerializer(addrss)
        return Response(serializer.data)
        
    def delete(self, request):
        address_id = request.data.get("address_id")
        user = request.user
        
        
        addrss = get_object_or_404(Address ,user=user, id=address_id)
        addrss.delete()
        
        
        return Response(status=status.HTTP_200_OK)
    
class CreatePaystackCheckoutSession(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        cart_code = request.COOKIES.get("cart_code")
        shipping_method = request.data.get("shipping_method")
        
        SHIPPING_PRICES = {
            "standard": Decimal("1500.00"),
            "express": Decimal("3000.00"),
        }

        if shipping_method not in SHIPPING_PRICES:
            return Response(
                {"error": "Invalid shipping method"},
                status=status.HTTP_400_BAD_REQUEST
            )

        shipping_fee = SHIPPING_PRICES[shipping_method]

        if not cart_code:
            return Response(
                {"error": "Cart not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = get_object_or_404(Cart, cart_code=cart_code)

        cart_items = cart.cartitems.select_related("product")

        if not cart_items.exists():
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Calculate total on backend (VERY IMPORTANT)
        cart_total  = Decimal("0.00")
        items_meta = []

        for item in cart_items:
            item_total = item.product.price * item.quantity
            cart_total  += item_total

            items_meta.append({
                "product_id": item.product.id,
                "name": item.product.name,
                "quantity": item.quantity,
                "unit_price": str(item.product.price),
            })
        total = cart_total + shipping_fee
        
        amount_kobo = int(total * 100)
        reference = f"purchase_{uuid.uuid4().hex}"

        checkout_data = {
            "email": user.email,
            "amount": amount_kobo,
            "currency": "NGN",
            "reference": reference,
            "callback_url": "http://localhost:3000/cart",
            "metadata": {
                "cart_code": str(cart.cart_code),
                "items": items_meta,
                "cancel_action": "https://next-shop-self.vercel.app/failed",
            },
            "label": f"Checkout for cart {cart.cart_code}",
        }

        success, result = checkout(checkout_data)

        if success:
            return Response(
                {
                    "authorization_url": result,
                    "reference": reference
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {"error": result},
            status=status.HTTP_400_BAD_REQUEST
        )
   
    
class PaystackWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        secret = settings.PAYSTACK_SECRET_KEY
        request_body = request.body

        # Compute HMAC signature
        computed_hash = hmac.new(secret.encode('utf-8'), request_body, hashlib.sha512).hexdigest()
        paystack_signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')

        if computed_hash != paystack_signature:
            return HttpResponse(status=400)  # Invalid signature

        # Parse the JSON payload
        webhook_post_data = json.loads(request_body)


        # Handle successful charge
        if webhook_post_data.get("event") == "charge.success":
            session = webhook_post_data["data"]
            metadata = session.get("metadata", {})
            cart_code = metadata.get("cart_code")

            # Call your fulfillment logic
            fulfill_checkout(session, cart_code)

        return HttpResponse(status=200)


def fulfill_checkout(session, cart_code):
    
    if Order.objects.filter(paystack_checkout_id=session["id"]).exists():
        return  # already processed

    order = Order.objects.create(paystack_checkout_id=session["id"],
        amount=session["amount"],
        currency=session["currency"],
        customer_email=session['customer']['email'],
        status="Paid")
    

    cart = Cart.objects.get(cart_code=cart_code)
    cartitems = cart.cartitems.all()

    for item in cartitems:
        orderitem = OrderItem.objects.create(order=order, product=item.product, 
                                             quantity=item.quantity)
    
    cart.cartitems.all().delete()

class OrderItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        
        email =user.email
        order_items = OrderItem.objects.filter(order__customer_email=email).select_related('order')
        serializer = OrderItemSerializer(order_items, many=True)
        return Response(serializer.data)