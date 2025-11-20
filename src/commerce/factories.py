from datetime import timedelta

import factory
from django.utils import timezone
from factory import fuzzy
from faker import Faker

from commerce.adapter.persistence.django_orm.models import Product, ProductStockEvents

fake = Faker("ko_KR")  # 한국어 로케일 사용


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    id = factory.Faker("bothify", text="PROD####??")
    name = factory.Sequence(lambda n: f"테스트 상품 {n}")
    description = factory.Faker("text", max_nb_chars=200)
    price = fuzzy.FuzzyFloat(1000.0, 100000.0, precision=2)


class ProductStockEventsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductStockEvents

    id = factory.Faker("bothify", text="EVT####??")
    product = factory.SubFactory(ProductFactory)
    change = fuzzy.FuzzyInteger(1, 1000)
    total_after_change = factory.LazyAttribute(lambda obj: obj.change)


class ProductDiscountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "commerce.ProductDiscount"

    id = factory.Faker("bothify", text="DISC####??")
    product = factory.SubFactory(ProductFactory)
    percentage = fuzzy.FuzzyFloat(5.0, 50.0, precision=2)
    start_date = factory.LazyFunction(lambda: timezone.now() - timedelta(days=10))
    end_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=30))
    active = True


class CuponFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "commerce.Cupons"

    id = factory.Faker("bothify", text="CUPON####??")
    code = factory.Faker("bothify", text="COUPON-####??")
    discount_percentage = fuzzy.FuzzyFloat(5.0, 30.0, precision=2)
    valid_from = factory.LazyFunction(lambda: timezone.now() - timedelta(days=5))
    valid_to = factory.LazyFunction(lambda: timezone.now() + timedelta(days=25))
    active = True
