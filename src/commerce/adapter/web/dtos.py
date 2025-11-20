from pydantic import BaseModel

from commerce.domain.entities import ProductEntity


class ProductDTO(BaseModel):
    id: str
    name: str
    description: str
    price: float
    stock_count: int
    discount_amount: float | None = None
    final_price: float | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock_count": self.stock_count,
            "discount_amount": self.discount_amount,
            "final_price": self.final_price,
        }


class ProductDetailDTO(BaseModel):
    product: ProductEntity
    product_discount_amount: float
    cupon_discount_amount: float
    final_price: float

    def to_dict(self) -> dict:
        return {
            "product": self.product.model_dump(mode="json"),
            "product_discount_amount": self.product_discount_amount,
            "cupon_discount_amount": self.cupon_discount_amount,
            "final_price": self.final_price,
        }
