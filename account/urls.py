
from django.urls import path

from . import views

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenVerifyView,
    TokenBlacklistView
)

from .views import (
    RegisterAPIView,
    EmailVerificationAPIView,
    ResendEmailVerificationAPIView,
    ResetPasswordAPIView,
    SetPasswordAPIView,
    LogoutView,
    GoogleAuth,
    CustomTokenObtainPairView,
    CookieTokenRefreshView,
    MeView
)

urlpatterns = [
    # urls.py
    path("api/auth/me", MeView.as_view(), name="auth-me"),

    path(
        "register", RegisterAPIView.as_view(), name="register"
    ),  # Register a new user endpoint
    path(
        "confirm_email/<str:token>",
        EmailVerificationAPIView.as_view(),
        name="confirm_email",
    ),
    path(
        "resend_confirm_email",
        ResendEmailVerificationAPIView.as_view(),
        name="resend_confirm_email",
    ),  # Resend confirm email endpoint
    path(
        "reset_password",
        ResetPasswordAPIView.as_view(),
        name="reset_password",
    ),  # Reset user password endpoint
    path(
        "set_password/<str:token>",
        SetPasswordAPIView.as_view(),
        name="set_password",
    ),  # Set user password after reset password endpoint
    path('logout', LogoutView.as_view(), name='auth_logout'),
    path('google_login', GoogleAuth.as_view(), name='google_login'),
    
    # JWT endpoints
    path("jwt/token", CustomTokenObtainPairView.as_view(), name="get_token"),
    path("jwt/token/refresh", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("jwt/token/verify", TokenVerifyView.as_view(), name="token_verify"),
    path('jwt/token/blacklist', TokenBlacklistView.as_view(), name='token_blacklist'),
    
]
