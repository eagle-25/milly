from datetime import datetime

from pydantic import BaseModel, field_validator

from common.utils import new_id


class ProductEntity(BaseModel):
    id: str
    name: str
    description: str
    price: float
    created_at: datetime
    updated_at: datetime

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("가격은 0보다 커야 합니다")
        return v

    @staticmethod
    def create(name: str, description: str, price: float) -> "ProductEntity":
        return ProductEntity(
            id=new_id(),
            name=name,
            description=description,
            price=price,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )


class ProductStockEventEntity(BaseModel):
    id: str
    product_id: str
    change: int
    total_after_change: int
    created_at: datetime
    version: int

    @staticmethod
    def create(
        product_id: str,
        change: int,
        total_after_change: int,
        version: int,
    ) -> "ProductStockEventEntity":
        return ProductStockEventEntity(
            id=new_id(),
            product_id=product_id,
            change=change,
            total_after_change=total_after_change,
            created_at=datetime.now(),
            version=version,
        )


class ProductDiscountEntity(BaseModel):
    id: str
    product_id: str
    percentage: float
    start_date: datetime
    end_date: datetime
    active: bool

    @staticmethod
    def create(
        product_id: str,
        percentage: float,
        start_date: datetime,
        end_date: datetime,
        active: bool = True,
    ) -> "ProductDiscountEntity":
        return ProductDiscountEntity(
            id=new_id(),
            product_id=product_id,
            percentage=percentage,
            start_date=start_date,
            end_date=end_date,
            active=active,
        )


class CuponEntity(BaseModel):
    id: str
    user_id: str
    code: str
    discount_percentage: float
    valid_from: datetime
    valid_to: datetime
    active: bool

    @staticmethod
    def create(
        user_id: str,
        code: str,
        discount_percentage: float,
        valid_from: datetime,
        valid_to: datetime,
        active: bool = True,
    ) -> "CuponEntity":
        return CuponEntity(
            id=new_id(),
            user_id=user_id,
            code=code,
            discount_percentage=discount_percentage,
            valid_from=valid_from,
            valid_to=valid_to,
            active=active,
        )


class ProductWithDiscountInfo(BaseModel):
    """상품 상세 정보 (할인 정보 포함) - 도메인 객체"""

    product: ProductEntity
    product_discount_amount: float
    cupon_discount_amount: float
    final_price: float
