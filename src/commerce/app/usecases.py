from collections.abc import Iterable
from datetime import datetime

from django.utils import timezone
from pydantic import BaseModel
from retry import retry

from commerce.app.ports.interfaces import (
    IProductPersistenceAdapter,
)
from commerce.app.services import CalcProductDiscountService
from commerce.domain.entities import (
    CuponEntity,
    ProductDiscountEntity,
    ProductEntity,
    ProductStockEventEntity,
    ProductWithDiscountInfo,
)
from commerce.domain.exceptions import InvalidStockChange
from common.exceptions import (
    DBOptimisticLockError,
    InvalidParameter,
    ServiceException,
)


class CreateProductUsecase:
    class Cmd(BaseModel):
        name: str
        description: str
        price: float
        stock: int

    def __init__(
        self,
        product_persistence_adapter: IProductPersistenceAdapter,
    ):
        self._product_persistence_adapter = product_persistence_adapter

    def execute(self, cmd: Cmd) -> tuple[ProductEntity, ProductStockEventEntity]:
        if cmd.price <= 0:
            raise InvalidParameter("price must be greater than 0.")
        if cmd.stock < 0:
            raise InvalidParameter("stock must be non-negative.")

        product = ProductEntity.create(
            name=cmd.name,
            description=cmd.description,
            price=cmd.price,
        )
        stock = ProductStockEventEntity.create(
            product_id=product.id,
            change=cmd.stock,
            total_after_change=cmd.stock,
            version=1,
        )
        return self._product_persistence_adapter.create_product(product, stock)


class UpdateProductStockUsecase:
    def __init__(
        self,
        product_persistence_adapter: IProductPersistenceAdapter,
    ):
        self._product_persistence_adapter = product_persistence_adapter

    @retry(
        tries=3,
        delay=0.2,
        backoff=2,
        exceptions=(DBOptimisticLockError,),
    )
    def execute(self, product_id: str, change: int) -> ProductStockEventEntity:
        if not (
            last_stock_event := self._product_persistence_adapter.get_last_stock_event(
                product_id
            )
        ):
            raise ServiceException("stock event not found.")

        if last_stock_event.total_after_change + change < 0:
            raise InvalidStockChange(f"insufficient stock for product {product_id}.")

        stock = ProductStockEventEntity.create(
            product_id=product_id,
            change=change,
            total_after_change=last_stock_event.total_after_change + change,
            version=last_stock_event.version + 1,
        )
        return self._product_persistence_adapter.create_product_stock_event(stock)


class UpsertProductDiscountUsecase:
    class Cmd(BaseModel):
        product_id: str
        percentage: float
        start_date: datetime
        end_date: datetime

    def __init__(
        self,
        product_persistence_adapter: IProductPersistenceAdapter,
    ):
        self._product_persistence_adapter = product_persistence_adapter

    def execute(self, cmd: Cmd) -> ProductDiscountEntity:
        discount = ProductDiscountEntity.create(
            product_id=cmd.product_id,
            percentage=cmd.percentage,
            start_date=cmd.start_date,
            end_date=cmd.end_date,
        )
        return self._product_persistence_adapter.create_product_discount(
            discount, deactivate_others=True
        )


class CreateCuponUsecase:
    class Cmd(BaseModel):
        user_id: str
        code: str
        valid_from: datetime
        discount_percentage: float
        valid_to: datetime

    def __init__(
        self,
        product_persistence_adapter: IProductPersistenceAdapter,
    ):
        self._product_persistence_adapter = product_persistence_adapter

    def execute(self, cmd: Cmd) -> CuponEntity:
        if cmd.valid_from >= cmd.valid_to:
            raise InvalidParameter("cupon valid period is invalid.")
        if not (self._product_persistence_adapter.is_user_exist(cmd.user_id)):
            raise InvalidParameter("user not found.")

        cupon = CuponEntity.create(
            code=cmd.code,
            user_id=cmd.user_id,
            discount_percentage=cmd.discount_percentage,
            valid_from=cmd.valid_from,
            valid_to=cmd.valid_to,
        )
        return self._product_persistence_adapter.create_cupon(cupon)


class GetProductsUsecase:
    class DTO(BaseModel):
        product: ProductEntity
        product_discount_amount: float
        total_amount: float
        stock_count: int

    def __init__(
        self,
        product_persistence_adapter: IProductPersistenceAdapter,
        calc_product_discount_service: CalcProductDiscountService,
    ):
        self._product_persistence_adapter = product_persistence_adapter
        self._calc_product_discount_service = calc_product_discount_service

    def execute(
        self, product_name: str | None, page_size: int = 30, page_index: int = 1
    ) -> Iterable[DTO]:
        for (
            product,
            product_discounts,
            stock_count,
        ) in self._product_persistence_adapter.get_products(
            product_name, page_size, page_index
        ):
            discount_amount = self._calc_product_discount_service.execute(
                product, product_discounts
            )
            total_amount = product.price - discount_amount
            yield self.DTO(
                product=product,
                product_discount_amount=discount_amount,
                total_amount=total_amount,
                stock_count=stock_count,
            )


class GetProductWithCuponDiscountUsecase:
    def __init__(
        self,
        product_persistence_adapter: IProductPersistenceAdapter,
        calc_product_discount_service: CalcProductDiscountService,
    ):
        self._product_persistence_adapter = product_persistence_adapter
        self._calc_product_discount_service = calc_product_discount_service

    def execute(
        self,
        user_id: str,
        product_id: str,
    ) -> ProductWithDiscountInfo:
        product, product_discounts = self._product_persistence_adapter.get_product(
            product_id
        )
        # 제품 기본 할인 계산
        product_discount_amount = self._calc_product_discount_service.execute(
            product, product_discounts
        )

        # 사용 가능한 쿠폰 조회 및 최대 할인 쿠폰 선택 (인증된 사용자만)
        max_discount_cupon = None
        if user_id != "anonymous" and user_id.isdigit():
            valid_coupons = (
                cupon
                for cupon in self._product_persistence_adapter.get_cupons(user_id)
                if cupon.active and cupon.valid_from <= timezone.now() <= cupon.valid_to
            )
            max_discount_cupon = (
                max(
                    valid_coupons,
                    key=lambda c: c.discount_percentage,
                )
                if valid_coupons
                else None
            )
        cupon_discount_amount = (product.price - product_discount_amount) * (
            max_discount_cupon.discount_percentage / 100 if max_discount_cupon else 0
        )

        # 최종 결제 금액 계산
        final_price = product.price - product_discount_amount - cupon_discount_amount
        return ProductWithDiscountInfo(
            product=product,
            product_discount_amount=product_discount_amount,
            cupon_discount_amount=cupon_discount_amount,
            final_price=final_price,
        )
