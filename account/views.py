from rest_framework import permissions
from rest_framework.generics import (
    CreateAPIView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import Http404
from rest_framework.views import APIView
from rest_framework import status, exceptions as drf_exceptions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from utils.jwt_token import token_decoder

from utils.email import EmailThread
from utils.jwt_token import token_generator
from .serializers import (
    RegisterSerializer,
    ResendEmailVerificationSerializer,
    ResetPasswordSerializer,
    SetPasswordSerializer,
    CustomTokenObtainPairSerializer
)

import requests
from rest_framework_simplejwt.authentication import JWTAuthentication
# Get the user from active model
User = get_user_model()


class RegisterAPIView(CreateAPIView):
    authentication_classes = []
    """Register a new user"""
    model = User
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class EmailVerificationAPIView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    """Confirm users email"""
    def get(self, request, token):
        # Decode the token to get the user id
        user_id = token_decoder(token)
        # Attempt to retrieve the user and activate the account
        try:
            user = get_object_or_404(User, pk=user_id)
            if user.is_verified:
                return Response(
                    {"message": "You are already verified"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.is_active = True
            user.is_verified = True
            user.save()
            return Response(
                {"message": "Account activated successfully!"},
                status=status.HTTP_200_OK,
            )
        except Http404:
            return Response(
                {"error": "Activation link is invalid!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TypeError:
            return Response(user_id)

class ResendEmailVerificationAPIView(APIView):
    authentication_classes = []
    """Resend a verification email to user"""

    permission_classes = [permissions.AllowAny]
    serializer_class = ResendEmailVerificationSerializer

    def post(self, request):
        serializer = ResendEmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            # Get user from serilizer validate method
            user = serializer.validated_data["user"]
            # Generate a jwt token for resend confirm email
            token = token_generator(user)
            # Resending confirm email token
            FRONTEND_URL = "http://localhost:3000"

            confirm_url = f"{FRONTEND_URL}/confirmation/{token['access']}"
            html_msg = f"""
                <p>Click below to confirm your email:</p>
                <p><a href="{confirm_url}">{confirm_url}</a></p>
            """

            EmailThread(user.email, "Confirm your email", html_msg).start()
            return Response(
                {"message": "The activation email has been sent again successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordAPIView(APIView):
    """Reset user password"""
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user: User = User.objects.get(email=email)
                
                if not user.is_verified:
                    return Response(
                    {"message": "You are not verified"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except User.DoesNotExist:
                return Response(
                    {"error": "User does not exist!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Generate a jwt token for reset password
            token = token_generator(user)
            # Sending reset password email token
            # set_password_url = self.request.build_absolute_uri(
            #     reverse("set_password", kwargs={"token": token["access"]})
            # )
            FRONTEND_URL = "https://todo-frontend-m4yu.onrender.com"

            confirm_url = f"{FRONTEND_URL}/auth/setpassword/{token['access']}"
            html_msg = f"""
                <p>for reset password click on:</p>
                <p><a href="{confirm_url}">{confirm_url}</a></p>
            """

            EmailThread(email, "Reset Password", html_msg).start()
            return Response(
                {"message: Reset password email has been sent!"},
                status=status.HTTP_200_OK,
            )

        return Response("")


class SetPasswordAPIView(APIView):
    authentication_classes = []
    """Set user password"""

    permission_classes = [permissions.AllowAny]
    serializer_class = SetPasswordSerializer

    def post(self, request, token):
        serializer = SetPasswordSerializer(data=request.data)
        # Decode the token to get the user id
        user_id = token_decoder(token)

        try:
            user = get_object_or_404(User, pk=user_id)
            
            if not user.is_verified:
                return Response(
                    {"message": "You are not verified"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Http404:
            return Response(
                {"error": "Activation link is invalid!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Token is not valid or expired
        except TypeError:
            return Response(user_id)

        if serializer.is_valid():
            new_password = serializer.validated_data["new_password"]
            user.set_password(new_password)
            user.save()
            return Response(
                {"message": "Your password has been changed successfully!"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   
class LogoutView(APIView):
    def post(self, request):
        try:
            # Get refresh token from the cookie instead of request.data
            refresh_token = request.COOKIES.get("refresh_token")
            if not refresh_token:
                return Response({"error": "No refresh token in cookies"}, status=status.HTTP_400_BAD_REQUEST)

            # Blacklist the token
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Create response and delete cookie
            response = Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
            response.delete_cookie("refresh_token")
            response.delete_cookie("access_token")

            return response

        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except drf_exceptions.AuthenticationFailed as exc:
            # exc.detail is the human message we raised above
            return Response({"detail": exc.detail}, status=getattr(exc, "status_code", status.HTTP_401_UNAUTHORIZED))
        except Exception as exc:
            # fallback for other errors
            return Response({"detail": "Authentication failed"}, status=status.HTTP_400_BAD_REQUEST)

        # success: validated_data contains access + refresh tokens
        data = serializer.validated_data
        refresh_token = data.get("refresh")

        # return access token in body (and store refresh token in cookie)
        response = Response({k: v for k, v in data.items() if k != "refresh"}, status=status.HTTP_200_OK)

        # cookie NOTE: for local dev use secure=False; set secure=True in production (HTTPS)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,      # set True in production with HTTPS
            samesite="Lax",    # use "None" if cross-site cookie + secure=True required
            path="/"
        )
        
        response.set_cookie(
    key="access_token",
    value=data.get("access"),
    httponly=True,
    secure=False,      # True in prod
    samesite="Lax",
    path="/",
    max_age=60 * 60 * 24 * 20,  # 20 days
)

        return response

   
class CookieTokenRefreshView(TokenRefreshView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get("refresh_token")

        if not refresh:
            return Response(
                {"error": "No refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.get_serializer(data={"refresh": refresh})
        serializer.is_valid(raise_exception=True)

        access = serializer.validated_data["access"]

        response = Response(status=status.HTTP_204_NO_CONTENT)

        response.set_cookie(
            key="access_token",
            value=access,
            httponly=True,
            secure=True,          # True in production
            samesite="Lax",
            path="/",
            max_age=60 * 10,      # 10 minutes
        )

        return response




class GoogleAuth(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        access_token = request.data.get("token")
        if not access_token:
            return Response({"error": "Token not provided", "status": False}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call Google userinfo endpoint with access_token
            userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
            response = requests.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                return Response({"error": "Invalid Google access token", "status": False},
                                status=status.HTTP_400_BAD_REQUEST)

            id_info = response.json()

            # Read user data
            email = id_info.get("email")
            first_name = id_info.get("given_name", "")
            last_name = id_info.get("family_name", "")
            profile_pic_url = id_info.get("picture", "")

            if not email:
                return Response({"error": "Google did not return an email", "status": False},
                                status=status.HTTP_400_BAD_REQUEST)

            # Create or update user
            user, created = User.objects.get_or_create(email=email)

            if created:
                user.set_unusable_password()
                user.first_name = first_name
                user.last_name = last_name
                user.username = first_name
                user.registration_method = "google"
                User.email = email
                user.is_active = True
                user.is_verified = True
                user.save()
            else:
                if user.registration_method != "google":
                    return Response({
                        "error": "User must sign in using email/password",
                        "status": False
                    }, status=status.HTTP_403_FORBIDDEN)

            # Create tokens
            refresh = RefreshToken.for_user(user)
            access = str(refresh.access_token)

            response = Response({
                "tokens": {
                    "access": access,
                    "refresh": str(refresh),
                },
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "status": True
            }, status=status.HTTP_200_OK)

            # Set HttpOnly cookie
            response.set_cookie(
                "refresh_token",
                str(refresh),
                httponly=True,
                secure=True,
                samesite="None",
                path="/"
            )
            
            response.set_cookie(
            "access_token",
            access,
            httponly=True,
            secure=True,
            samesite="None",
            path="/"
        )


            return response

        except Exception as e:
            print("ERROR:", e)
            return Response({"error": "Authentication failed", "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }, status=status.HTTP_200_OK)