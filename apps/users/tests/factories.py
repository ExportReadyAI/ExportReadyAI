"""
Test Factories for Users App
"""

import factory
from faker import Faker

from apps.users.models import User, UserRole

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.LazyAttribute(lambda _: fake.unique.email())
    full_name = factory.LazyAttribute(lambda _: fake.name())
    role = UserRole.UMKM
    is_active = True
    is_staff = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or "testpass123"
        self.set_password(password)
        if create:
            self.save()


class AdminUserFactory(UserFactory):
    """Factory for creating Admin User instances."""

    role = UserRole.ADMIN
    is_staff = True


class UMKMUserFactory(UserFactory):
    """Factory for creating UMKM User instances."""

    role = UserRole.UMKM

