from collections.abc import Iterable

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from commerce.adapter.persistence.django_orm.models import (
    Cupons,
    Product,
    ProductDiscount,
    ProductStockEvents,
)
from commerce.app.ports.interfaces import IProductPersistenceAdapter
from commerce.domain.entities import (
    CuponEntity,
    ProductDiscountEntity,
    ProductEntity,
    ProductStockEventEntity,
)
from common.exceptions import DBOptimisticLockError


class DjangoORMPersistenceAdapter(IProductPersistenceAdapter):
    @transaction.atomic
    def create_product(self, product_entity, stock_event):
        orm_product = Product.from_domain(product_entity)
        orm_product.save()
        orm_stock_event = ProductStockEvents.from_domain(stock_event)
        orm_stock_event.save()
        return Product.to_domain(orm_product), ProductStockEvents.to_domain(
            orm_stock_event
        )

    def create_product_stock_event(
        self, stock_event: ProductStockEventEntity
    ) -> ProductStockEventEntity:
        try:
            with transaction.atomic():
                orm_stock_event = ProductStockEvents.from_domain(stock_event)
                orm_stock_event.save()
                return ProductStockEvents.to_domain(orm_stock_event)
        except IntegrityError as e:
            if "unique constraint" in str(e).lower():
                raise DBOptimisticLockError
            raise

    def get_last_stock_event(self, product_id: str) -> ProductStockEventEntity | None:
        orm_stock_event = (
            ProductStockEvents.objects.filter(product_id=product_id)
            .order_by("-version")
            .first()
        )
        if orm_stock_event is None:
            return None
        return ProductStockEvents.to_domain(orm_stock_event)

    @transaction.atomic
    def create_product_discount(
        self, discount: ProductDiscountEntity, deactivate_others: bool = False
    ) -> ProductDiscountEntity:
        if deactivate_others:
            ProductDiscount.objects.filter(
                product_id=discount.product_id,
                active=True,
            ).update(active=False)

        orm_discount = ProductDiscount.from_domain(discount)
        orm_discount.save()
        return ProductDiscount.to_domain(orm_discount)

    def create_cupon(self, cupon: CuponEntity) -> CuponEntity:
        orm_cupon = Cupons.from_domain(cupon)
        orm_cupon.save()
        return Cupons.to_domain(orm_cupon)

    def get_products(
        self, product_name: str | None, page_size: int = 30, cur_page: int = 1
    ) -> Iterable[
        tuple[ProductEntity, Iterable[ProductDiscountEntity], int]
    ]:  # product, product_discounts, stock_count
        query = Product.objects.all()
        if product_name:
            query = query.filter(name__icontains=product_name)
        products = query[(cur_page - 1) * page_size : cur_page * page_size]

        for orm_product in products:
            product_entity = Product.to_domain(orm_product)
            discounts = [
                ProductDiscount.to_domain(discount)
                for discount in ProductDiscount.objects.filter(
                    product_id=orm_product.id, active=True
                )
            ]
            stock_count = (
                ProductStockEvents.objects.filter(product_id=orm_product.id)
                .order_by("-version")
                .first()
            )
            total_stock = stock_count.total_after_change if stock_count else 0
            yield (product_entity, discounts, total_stock)

    def get_product(
        self, product_id: str
    ) -> tuple[ProductEntity, Iterable[ProductDiscountEntity]]:
        orm_product = Product.objects.get(id=product_id)
        product_entity = Product.to_domain(orm_product)
        discounts = [
            ProductDiscount.to_domain(discount)
            for discount in ProductDiscount.objects.filter(
                product_id=orm_product.id, active=True
            )
        ]
        return product_entity, discounts

    def get_cupons(self, user_id: str) -> Iterable[CuponEntity]:
        orm_cupons = Cupons.objects.filter(user_id=user_id, active=True)
        for orm_cupon in orm_cupons:
            yield Cupons.to_domain(orm_cupon)

    def is_user_exist(self, user_id: str) -> bool:
        User = get_user_model()
        return User.objects.filter(id=user_id).exists()
