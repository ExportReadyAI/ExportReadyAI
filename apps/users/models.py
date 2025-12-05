"""
User Model for ExportReady.AI

Custom User model with email as the primary identifier.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserRole(models.TextChoices):
    """
    User roles in the system.
    """

    ADMIN = "Admin", "Administrator"
    UMKM = "UMKM", "UMKM (Pelaku Usaha)"


class UserManager(BaseUserManager):
    """
    Custom manager for User model with email as the unique identifier.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        # Normalize email and ensure full lowercase to match tests expectations
        email = self.normalize_email(email).lower()
        extra_fields.setdefault("role", UserRole.UMKM)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for ExportReady.AI.
    
    Uses email as the primary identifier instead of username.
    
    Fields:
        - id: Primary key (auto-generated)
        - email: Unique email address
        - password: Hashed password (inherited from AbstractBaseUser)
        - full_name: User's full name
        - role: User role (Admin or UMKM)
        - created_at: Timestamp when user was created
        - is_active: Whether the user account is active
        - is_staff: Whether the user can access admin site
    """

    email = models.EmailField(
        "email address",
        unique=True,
        db_index=True,
        error_messages={
            "unique": "A user with this email already exists.",
        },
    )
    full_name = models.CharField("full name", max_length=255)
    role = models.CharField(
        "role",
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.UMKM,
    )
    created_at = models.DateTimeField("created at", auto_now_add=True)
    updated_at = models.DateTimeField("updated at", auto_now=True)

    # Django auth fields
    is_active = models.BooleanField("active", default=True)
    is_staff = models.BooleanField("staff status", default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.email.split("@")[0]

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_umkm(self):
        return self.role == UserRole.UMKM

