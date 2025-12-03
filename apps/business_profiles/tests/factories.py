"""
Test Factories for Business Profiles App
"""

import factory
from faker import Faker

from apps.business_profiles.models import BusinessProfile
from apps.users.tests.factories import UMKMUserFactory

fake = Faker()


class BusinessProfileFactory(factory.django.DjangoModelFactory):
    """Factory for creating BusinessProfile instances."""

    class Meta:
        model = BusinessProfile

    user = factory.SubFactory(UMKMUserFactory)
    company_name = factory.LazyAttribute(lambda _: fake.company())
    address = factory.LazyAttribute(lambda _: fake.address())
    production_capacity_per_month = factory.LazyAttribute(lambda _: fake.random_int(min=100, max=10000))
    certifications = factory.LazyAttribute(lambda _: [])
    year_established = factory.LazyAttribute(lambda _: fake.random_int(min=1990, max=2024))

