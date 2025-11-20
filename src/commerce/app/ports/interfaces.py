from collections.abc import Iterable
from typing import Protocol

from commerce.domain.entities import (
    CuponEntity,
    ProductDiscountEntity,
    ProductEntity,
    ProductStockEventEntity,
)


class IProductPersistenceAdapter(Protocol):
    def create_product(
        self,
        product: ProductEntity,
        stock_event: ProductStockEventEntity,
    ) -> tuple[ProductEntity, ProductStockEventEntity]: ...

    def create_product_stock_event(
        self, stock_event: ProductStockEventEntity
    ) -> ProductStockEventEntity: ...

    def get_last_stock_event(
        self, product_id: str
    ) -> ProductStockEventEntity | None: ...

    def create_product_discount(
        self, discount: ProductDiscountEntity, deactivate_others: bool = False
    ) -> ProductDiscountEntity: ...

    def create_cupon(self, cupon: CuponEntity) -> CuponEntity: ...

    def get_products(
        self, product_name: str | None, page_size: int = 30, page_index: int = 1
    ) -> Iterable[
        tuple[ProductEntity, Iterable[ProductDiscountEntity], int]
    ]:  # product, product_discounts, stock_count
        ...

    def get_product(
        self, product_id: str
    ) -> tuple[
        ProductEntity, Iterable[ProductDiscountEntity]
    ]:  # product, product_discounts
        ...

    def get_cupons(self, user_id: str) -> Iterable[CuponEntity]: ...

    def is_user_exist(self, user_id: str) -> bool: ...
