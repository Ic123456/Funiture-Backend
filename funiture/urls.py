from django.urls import path
# from rest_framework_simplejwt.views import (
#     TokenVerifyView,
#     TokenBlacklistView
# )
from . import views

urlpatterns = [
    # path("profile", views.GetUserView.as_view(), name="profile"),
    path("getemail", views.InputEmailCreateView.as_view(), name="getemail"),
    path("cart", views.CartView.as_view(), name="cart"),
    path("recent", views.RecentlyViewedApiView.as_view(), name="recent"),
    path("profile", views.Profileview.as_view(), name="profile"),
    path("getwishlist", views.WishListView.as_view(), name="wishlist"),
    path("wishlistdetail", views.WishListDetailedView.as_view(), name="wishlistDetail"),
    path("product_list", views.ProductListAPIView.as_view(), name="product_list"),
    path("get_product_list", views.GetProductListAPIView.as_view(), name="product_list"),
    path("products/<slug:slug>", views.ProductDetailView.as_view(), name="product_detail"),
    
    path("category_list", views.CategoryListAPIView.as_view(), name="category_list"),
    
    path("add_to_cart", views.AddToCart.as_view(), name="add_to_cart"),
   
    path("update_cartitem", views.CartDetailedView.as_view(), name="update_cartitem"),


    path("add_to_wishlist", views.AddToWishListView.as_view(), name="add_to_wishlist"),
    path("address", views.AddressView.as_view(), name="address"),
    path("search", views.ProductSearchView.as_view(), name="search"),
    
    path("create_paystack_checkout_session", views.CreatePaystackCheckoutSession.as_view(), name="create_paystack_checkout_session"),
    path('webhook/paystack/', views.PaystackWebhookView.as_view(), name="paystack_webhook"),
    path("orderitem", views.OrderItemView.as_view(), name="orderitem"),
    
]