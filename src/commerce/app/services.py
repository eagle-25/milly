# 복잡한 비즈니스 로직 재사용 위한 서비스 계층

from collections.abc import Iterable

from commerce.domain.entities import (
    ProductDiscountEntity,
    ProductEntity,
)
from common.exceptions import ServiceException


class CalcProductDiscountService:
    def execute(
        self,
        product: ProductEntity,
        discounts: Iterable[ProductDiscountEntity],
    ) -> float:
        if any(discount.product_id != product.id for discount in discounts):
            raise ServiceException("Product and Discount do not match.")

        applicable_discounts = [discount for discount in discounts if discount.active]
        if not applicable_discounts:
            return 0.0
        max_discount = max(discount.percentage for discount in applicable_discounts)
        discount_amount = product.price * (max_discount / 100)
        return discount_amount
