from datetime import datetime, timedelta
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from commerce.adapter.persistence.django_orm.django_orm_persistence_adpater import (
    DjangoORMPersistenceAdapter,
)
from commerce.adapter.web.dtos import ProductDTO
from commerce.app.services import CalcProductDiscountService
from commerce.app.usecases import (
    CreateCuponUsecase,
    CreateProductUsecase,
    GetProductsUsecase,
    GetProductWithCuponDiscountUsecase,
    UpdateProductStockUsecase,
    UpsertProductDiscountUsecase,
)
from common.decorators import parse_json_form_body
from common.utils import get_or_raise, parse_datetime_with_default


@require_http_methods(["GET"])
def get_product_detail_view(request: HttpRequest, product_id: str) -> JsonResponse:
    usecase = GetProductWithCuponDiscountUsecase(
        product_persistence_adapter=DjangoORMPersistenceAdapter(),
        calc_product_discount_service=CalcProductDiscountService(),
    )
    # 익명 사용자인 경우 기본 user_id 사용
    user_id = str(request.user.id) if request.user.is_authenticated else "anonymous"  # type: ignore
    res = usecase.execute(
        user_id=user_id,
        product_id=product_id,
    )

    # 도메인 객체를 DTO로 변환
    from commerce.adapter.web.dtos import ProductDetailDTO

    dto = ProductDetailDTO(
        product=res.product,
        product_discount_amount=res.product_discount_amount,
        cupon_discount_amount=res.cupon_discount_amount,
        final_price=res.final_price,
    )
    return JsonResponse(dto.to_dict())


class ProductsView(View):
    """상품 목록 조회 및 생성"""

    def get(self, request: HttpRequest) -> JsonResponse:
        """상품 목록 조회"""
        # parse
        product_name = request.GET.get("product_name")
        page_size = int(request.GET.get("page_size", 30))
        page_index = int(request.GET.get("page_index", 1))

        # execute
        product_persistence_adapter = DjangoORMPersistenceAdapter()
        usecase = GetProductsUsecase(
            product_persistence_adapter=product_persistence_adapter,
            calc_product_discount_service=CalcProductDiscountService(),
        )
        results = usecase.execute(
            product_name=product_name,
            page_size=page_size,
            page_index=page_index,
        )

        # resp
        dtos = []
        for result in results:
            dto = ProductDTO(
                id=result.product.id,
                name=result.product.name,
                description=result.product.description,
                price=result.product.price,
                stock_count=result.stock_count,
                discount_amount=result.product_discount_amount,
                final_price=result.total_amount,
            )
            dtos.append(dto.to_dict())
        return JsonResponse({"products": dtos})

    @method_decorator(parse_json_form_body)
    def post(self, request: HttpRequest, payload: dict[str, Any]) -> JsonResponse:
        """상품 생성"""
        # parse
        name = get_or_raise(payload, "name")
        description = get_or_raise(payload, "description")
        price = get_or_raise(payload, "price")
        stock = get_or_raise(payload, "stock")

        # execute
        usecase = CreateProductUsecase(
            product_persistence_adapter=DjangoORMPersistenceAdapter()
        )
        product, stock_event = usecase.execute(
            CreateProductUsecase.Cmd(
                name=name, description=description, price=price, stock=stock
            )
        )

        # resp
        dto = ProductDTO(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            stock_count=stock_event.total_after_change,
        )
        return JsonResponse(dto.to_dict())


@require_http_methods(["POST"])
@parse_json_form_body
def update_product_stock_view(
    request: HttpRequest, payload: dict[str, Any], product_id: str
) -> JsonResponse:
    # parse
    stock_change = get_or_raise(payload, "change")

    # execute
    product_persistence_adapter = DjangoORMPersistenceAdapter()
    usecase = UpdateProductStockUsecase(
        product_persistence_adapter=product_persistence_adapter,
    )
    stock_event = usecase.execute(
        product_id=product_id,
        change=stock_change,
    )

    # resp
    return JsonResponse({"new_stock_count": stock_event.total_after_change})


@require_http_methods(["POST"])
@parse_json_form_body
def upsert_product_discount_view(
    request: HttpRequest, payload: dict[str, Any], product_id: str
) -> JsonResponse:
    # parse
    percentage = get_or_raise(payload, "percentage")

    # execute
    usecase = UpsertProductDiscountUsecase(
        product_persistence_adapter=DjangoORMPersistenceAdapter(),
    )
    discount = usecase.execute(
        UpsertProductDiscountUsecase.Cmd(
            product_id=product_id,
            percentage=percentage,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
    )

    # resp
    return JsonResponse(
        {
            "discount_id": discount.id,
            "product_id": discount.product_id,
            "percentage": discount.percentage,
            "is_active": discount.active,
        }
    )


@require_http_methods(["POST"])
@parse_json_form_body
def create_cupon_view(request: HttpRequest, payload: dict[str, Any]) -> JsonResponse:
    # 쿠폰 생성은 인증된 사용자만 가능
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Authentication required for coupon creation"}, status=401
        )

    # parse
    discount_percentage = get_or_raise(payload, "discount_percentage")
    code = payload.get("code", f"COUPON_{datetime.now().timestamp()}")
    valid_from = parse_datetime_with_default(str(get_or_raise(payload, "valid_from")))
    valid_to = parse_datetime_with_default(str(get_or_raise(payload, "valid_to")))
    

    # execute
    product_persistence_adapter = DjangoORMPersistenceAdapter()
    usecase = CreateCuponUsecase(
        product_persistence_adapter=product_persistence_adapter,
    )
    # 인증된 사용자만 여기까지 올 수 있음
    cupon = usecase.execute(
        CreateCuponUsecase.Cmd(
            user_id=str(request.user.id),  # type: ignore
            code=code,
            discount_percentage=float(discount_percentage),
            valid_from=valid_from,
            valid_to=valid_to,
        )
    )

    # resp
    return JsonResponse(
        {
            "cupon_id": cupon.id,
            "user_id": cupon.user_id,
            "code": cupon.code,
            "discount_percentage": cupon.discount_percentage,
        }
    )
