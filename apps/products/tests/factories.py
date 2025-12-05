import factory
from faker import Faker

from apps.business_profiles.models import BusinessProfile
from apps.users.models import User, UserRole
from apps.products.models import Product, ProductEnrichment


fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@test.com")
    full_name = factory.Faker("name")
    role = UserRole.UMKM
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "defaultpassword123")
        obj = model_class(*args, **kwargs)
        obj.set_password(password)
        obj.save()
        return obj


class BusinessProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BusinessProfile

    user = factory.SubFactory(UserFactory)
    company_name = factory.Faker("company")
    address = factory.Faker("address")
    production_capacity_per_month = factory.Faker("pyint", min_value=100, max_value=10000)
    year_established = factory.Faker("year_int")


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    business = factory.SubFactory(BusinessProfileFactory)
    name_local = factory.Faker("word")
    category_id = 1
    description_local = factory.Faker("text")
    material_composition = "Cotton, Polyester"
    production_technique = "Machine"
    finishing_type = "Natural Polish"
    quality_specs = {"moisture": "5%", "tolerance": "±2mm"}
    durability_claim = "12 Bulan"
    packaging_type = "Karton"
    dimensions_l_w_h = {"l": 20, "w": 15, "h": 5}
    weight_net = "0.150"
    weight_gross = "0.170"


class ProductEnrichmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductEnrichment

    product = factory.SubFactory(ProductFactory)
    hs_code_recommendation = "61059000"
    sku_generated = "TAX-MAT-001"
    name_english_b2b = "Premium Textile Product"
    description_english_b2b = "High quality textile for export"
    marketing_highlights = ["Handmade", "High Quality", "Sustainable"]
