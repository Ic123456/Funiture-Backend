from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email) #user@EXAMPLE.COM will be user@example.com
        user = self.model(email=email, **extra_fields) #Creates a new User instance in memory (not saved yet)
        user.set_password(password) #This takes the plain password and hashes it securely
        user.save(using=self._db) #Saves it to the database
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        """We dont need password bcs we are logging user with EMAIL and OTP"""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_verified", False)
        extra_fields.setdefault("is_active", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

REGISTRATION_CHOICES = [
    ('email', 'Email'),
    ('google', 'Google')
]

class User(AbstractUser):
    """User model."""
    username = models.CharField(null=True, blank=True, max_length=50)
    email = models.EmailField(_("email address"), unique=True)
    is_verified = models.BooleanField(_("verified"), default=False)

    USERNAME_FIELD = "email" # use email as the login identifier (instead of username)
    REQUIRED_FIELDS = [] #(["full_name"]), will be added when creating superuser, [] email and password

    registration_method = models.CharField(max_length=20, choices=REGISTRATION_CHOICES, default='email')


    # Custom user manager
    objects = UserManager() #Connects this User model to your custom UserManagerere.