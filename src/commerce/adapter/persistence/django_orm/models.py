from django.contrib.auth.models import User
from django.db import models

from commerce.domain.entities import (
    CuponEntity,
    ProductDiscountEntity,
    ProductEntity,
    ProductStockEventEntity,
)


# Create your models here.
class Product(models.Model):
    id = models.CharField(primary_key=True, max_length=18)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def from_domain(cls, product: ProductEntity) -> "Product":
        return cls(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            # created_at과 updated_at은 auto_now_add=True, auto_now=True로 자동 설정
        )

    @classmethod
    def to_domain(cls, orm_product: "Product") -> ProductEntity:
        return ProductEntity(
            id=orm_product.id,
            name=orm_product.name,
            description=orm_product.description,
            price=float(orm_product.price),
            created_at=orm_product.created_at,
            updated_at=orm_product.updated_at,
        )


class ProductStockEvents(models.Model):
    id = models.CharField(primary_key=True, max_length=18)
    product = models.ForeignKey(
        Product,
        on_delete=models.DO_NOTHING,
        related_name="stock_events",
    )
    change = models.IntegerField()
    total_after_change = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    version = models.IntegerField()

    class Meta:
        unique_together = ("product", "version")

    @classmethod
    def from_domain(cls, stock_event: ProductStockEventEntity) -> "ProductStockEvents":
        return cls(
            id=stock_event.id,
            product=Product(id=stock_event.product_id),
            change=stock_event.change,
            total_after_change=stock_event.total_after_change,
            # created_at은 auto_now_add=True로 자동 설정
            version=stock_event.version,
        )

    @classmethod
    def to_domain(cls, orm_stock_event: "ProductStockEvents"):
        return ProductStockEventEntity(
            id=orm_stock_event.id,
            product_id=orm_stock_event.product.id,
            change=orm_stock_event.change,
            total_after_change=orm_stock_event.total_after_change,
            created_at=orm_stock_event.created_at,
            version=orm_stock_event.version,
        )


class ProductDiscount(models.Model):
    id = models.CharField(primary_key=True, max_length=18)
    product = models.ForeignKey(
        Product,
        on_delete=models.DO_NOTHING,
        related_name="discounts",
    )
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)

    @classmethod
    def from_domain(cls, discount: ProductDiscountEntity) -> "ProductDiscount":
        return cls(
            id=discount.id,
            product=Product(id=discount.product_id),
            percentage=discount.percentage,
            start_date=discount.start_date,
            end_date=discount.end_date,
            active=discount.active,
        )

    @classmethod
    def to_domain(cls, orm_discount: "ProductDiscount"):
        return ProductDiscountEntity(
            id=orm_discount.id,
            product_id=orm_discount.product.id,
            percentage=float(orm_discount.percentage),
            start_date=orm_discount.start_date,
            end_date=orm_discount.end_date,
            active=orm_discount.active,
        )


class Cupons(models.Model):
    id = models.CharField(primary_key=True, max_length=18)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
        ]

    @classmethod
    def from_domain(cls, cupon: CuponEntity) -> "Cupons":
        return cls(
            id=cupon.id,
            user=User(id=int(cupon.user_id)),
            code=cupon.code,
            discount_percentage=cupon.discount_percentage,
            valid_from=cupon.valid_from,
            valid_to=cupon.valid_to,
            active=cupon.active,
        )

    @classmethod
    def to_domain(cls, orm_cupon: "Cupons"):
        return CuponEntity(
            id=orm_cupon.id,
            user_id=str(orm_cupon.user.id),
            code=orm_cupon.code,
            discount_percentage=float(orm_cupon.discount_percentage),
            valid_from=orm_cupon.valid_from,
            valid_to=orm_cupon.valid_to,
            active=orm_cupon.active,
        )
