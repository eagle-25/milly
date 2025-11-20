import json

import pytest

from commerce.adapter.persistence.django_orm.django_orm_persistence_adpater import (
    DjangoORMPersistenceAdapter,
)
from commerce.adapter.persistence.django_orm.models import (
    Cupons,
    Product,
    ProductDiscount,
    ProductStockEvents,
)
from commerce.factories import (
    CuponFactory,
    ProductDiscountFactory,
    ProductFactory,
    ProductStockEventsFactory,
)


def _create_sample_product() -> ProductFactory:
    p = ProductFactory()
    ProductStockEventsFactory(product=p, version=1)

    return p


# === 상품 테스트 ===


@pytest.mark.django_db
def test_상품을_생성한다(authed_client):
    # arrange
    product_data = {
        "name": "테스트 상품",
        "description": "테스트 상품 설명",
        "price": 10000.0,
        "stock": 100,
    }

    # act
    response = authed_client.post(
        path="/commerce/products/",
        data=json.dumps(product_data),
        content_type="application/json",
    )
    # assert
    assert response.status_code == 200

    product = Product.objects.all()
    assert product.count() == 1
    product = product[0]
    assert product.name == "테스트 상품"

    events = ProductStockEvents.objects.filter(product=product)
    assert events.count() == 1
    event = events[0]
    assert event.total_after_change == 100
    assert event.change == 100


@pytest.mark.django_db
def test_상품_가격이_음수면_생성에_실패한다(authed_client):
    # arrange
    product_data = {
        "name": "테스트 상품",
        "description": "테스트 상품 설명",
        "price": -1000.0,
        "stock": 100,
    }

    # act
    response = authed_client.post(
        path="/commerce/products/",
        data=json.dumps(product_data),
        content_type="application/json",
    )
    # assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_재고가_음수면_생성에_실패한다(authed_client):
    # arrange
    product_data = {
        "name": "테스트 상품",
        "description": "테스트 상품 설명",
        "price": 10000.0,
        "stock": -10,
    }

    # act
    response = authed_client.post(
        path="/commerce/products/",
        data=json.dumps(product_data),
        content_type="application/json",
    )
    # assert
    assert response.status_code == 400


# === 재고 테스트 ===


@pytest.mark.django_db
def test_상품_재고를_수정한다(authed_client):
    # arrange
    product = ProductFactory()
    ProductStockEventsFactory(
        product=product,
        change=100,
        version=1,
    )

    # act
    response = authed_client.post(
        path=f"/commerce/products/{product.id}/stock/",
        data=json.dumps({"change": 50}),
        content_type="application/json",
    )

    # assert
    assert response.status_code == 200

    ProductStockEvents.objects.filter(product=product).order_by("-version")
    events = ProductStockEvents.objects.filter(product=product).order_by("-version")
    assert events.count() == 2
    latest_event = events[0]
    assert latest_event.total_after_change == 150
    assert latest_event.change == 50


@pytest.mark.django_db
def test_재고_이벤트가_없으면_수정에_실패한다(authed_client):
    # arrange
    product = ProductFactory()

    # act
    response = authed_client.post(
        path=f"/commerce/products/{product.id}/stock/",
        data=json.dumps({"change": 50}),
        content_type="application/json",
    )

    # assert
    assert response.status_code == 500


@pytest.mark.django_db
def test_재고가_음수로_변경되면_실패한다(authed_client):
    # arrange
    product = ProductFactory()
    ProductStockEventsFactory(
        product=product,
        change=30,
        version=1,
    )

    # act
    response = authed_client.post(
        path=f"/commerce/products/{product.id}/stock/",
        data=json.dumps({"change": -50}),
        content_type="application/json",
    )

    # assert
    assert response.status_code == 400


@pytest.mark.django_db
def test_동시성_문제_발생시_재시도_후_성공한다(authed_client, mocker):
    # arrange
    product = ProductFactory()
    # 초기 재고 이벤트 (version 1)
    v1 = ProductStockEventsFactory(
        product=product,
        change=100,
        total_after_change=100,
        version=1,
    )
    # 다른 사용자가 추가한 이벤트 (version 2)
    v2 = ProductStockEventsFactory(
        product=product,
        change=100,
        total_after_change=200,  # 100 + 100
        version=2,
    )

    mocker.patch(
        "commerce.adapter.web.views.DjangoORMPersistenceAdapter.get_last_stock_event",
        side_effect=[
            v1,
            v2,
        ],  # 첫번째 호출: v1(outdated), 두번째 호출: v2(latest) | 원래는 v2 부터 반환해야함
    )
    spy = mocker.spy(DjangoORMPersistenceAdapter, "create_product_stock_event")

    # act
    response = authed_client.post(
        path=f"/commerce/products/{product.id}/stock/",
        data=json.dumps({"change": 20}),
        content_type="application/json",
    )

    # assert
    assert response.status_code == 200

    # create_product_stock_event이 2번 호출되어야 함 (1번 실패 + 1번 성공), 재시도 검증
    assert spy.call_count == 2
    called_versions = [call.args[1].version for call in spy.call_args_list]
    assert called_versions == [2, 3]

    # 재고 이벤트가 3개 있어야 함 (version 1, 2, 3)
    events = ProductStockEvents.objects.filter(product=product).order_by("version")
    assert [event.version for event in events] == [1, 2, 3]
    assert events[2].total_after_change == 220


@pytest.mark.django_db
def test_전체_상품_목록을_조회한다(authed_client):
    # arrange
    products = [_create_sample_product() for _ in range(3)]

    # act
    response = authed_client.get(
        path="/commerce/products/",
    )

    # assert
    assert response.status_code == 200

    # 재고랑 상품 목록 맞게 반환하는지 확인
    found = response.json()["products"]
    for i, prod in enumerate(products):
        assert found[i]["id"] == prod.id
        assert (
            found[i]["stock_count"]
            == prod.stock_events.latest("version").total_after_change
        )


@pytest.mark.django_db
def test_제품_이름으로_상품을_검색한다(authed_client):
    # arrange
    [ProductFactory(name=f"pn_{i}") for i in range(3)]
    ProductFactory(name="other_name")

    # act
    response = authed_client.get(
        path="/commerce/products/",
        data={"product_name": "pn"},
    )

    # assert
    assert response.status_code == 200

    # 목록 맞게 반환하는지 확인
    found = response.json()["products"]
    for x in found:
        assert "pn" in x["name"]


@pytest.mark.django_db
def test_제품_목록_조회시_페지네이션이_동작하는지_확인한다(authed_client):
    # arrange
    total_products = 25
    page_size = 10
    [ProductFactory(name=f"pn_{i}") for i in range(total_products)]

    # act, assert
    left = total_products
    for i in range((total_products // page_size) + 1):
        page_index = i + 1
        response = authed_client.get(
            path="/commerce/products/",
            data={
                "page_size": page_size,
                "page_index": page_index,
            },
        )

        assert response.status_code == 200
        assert len(response.json()["products"]) == min(page_size, left)
        left -= page_size


# === 상품 할인 테스트 ===


@pytest.mark.django_db
def test_상품_할인을_생성한다(authed_client):
    # arrange
    product = ProductFactory()

    discount_data = {
        "percentage": 20.0,
        "is_active": True,
    }

    # act
    response = authed_client.post(
        path=f"/commerce/products/{product.id}/discounts/",
        data=json.dumps(discount_data),
        content_type="application/json",
    )

    # assert
    assert response.status_code == 200

    discounts = ProductDiscount.objects.filter(product=product)
    assert discounts.count() == 1
    assert discounts[0].percentage == 20.0


@pytest.mark.django_db
def test_상품_할인을_다시_생성하면_기존_할인이_비활성화된다(authed_client):
    # arrange
    product = ProductFactory()

    existing_discount = ProductDiscountFactory(product=product)

    new_discount_data = {"percentage": 20.0}

    # act
    response = authed_client.post(
        path=f"/commerce/products/{product.id}/discounts/",
        data=json.dumps(new_discount_data),
        content_type="application/json",
    )

    # assert
    assert response.status_code == 200

    existing_discount.refresh_from_db()
    assert existing_discount.active is False

    discounts = ProductDiscount.objects.filter(product=product)
    assert discounts.count() == 2
    new_discount = discounts.get(percentage=20.0, active=True)
    assert new_discount.active is True


@pytest.mark.django_db
def test_상품_목록_조회시_기본_할인이_반영된다(authed_client):
    # arrange
    product = ProductFactory(
        price=10000.0,
    )
    ProductDiscountFactory(
        product=product,
        percentage=10.0,
    )

    # act
    response = authed_client.get(
        path="/commerce/products/",
    )
    # assert
    assert response.status_code == 200

    products = response.json()["products"]
    assert len(products) == 1
    assert products[0]["discount_amount"] == 1000.0
    assert products[0]["final_price"] == 9000.0


@pytest.mark.django_db
def test_상품_상세_조회시_사용자가_가진_쿠폰까지_반영된다(authed_client, test_user):
    # arrange
    product = ProductFactory(
        price=20000.0,
    )
    ProductDiscountFactory(
        product=product,
        percentage=10.0,
    )
    CuponFactory(
        user=test_user,
        discount_percentage=10.0,
    )

    # act
    response = authed_client.get(
        path=f"/commerce/products/{product.id}/",
    )

    # assert
    assert response.status_code == 200
    product_detail = response.json()
    assert product_detail["product"]["price"] == 20000.0
    assert product_detail["product_discount_amount"] == 2000.0  # 10
    assert product_detail["cupon_discount_amount"] == 1800.0  # 10% of 18000
    assert product_detail["final_price"] == 16200.0


# === 쿠폰 테스트 ===
@pytest.mark.django_db
def test_쿠폰을_생성한다(authed_client):
    # arrange
    ProductFactory()
    cupon_data = {
        "code": "DISCOUNT20",
        "discount_percentage": 20.0,
        "valid_from": "2024-01-01T00:00:00Z",
        "valid_to": "2024-12-31T23:59:59Z",
    }

    # act
    response = authed_client.post(
        path="/commerce/coupons/",
        data=json.dumps(cupon_data),
        content_type="application/json",
    )

    # assert
    assert response.status_code == 200

    cupons = Cupons.objects.all()
    assert cupons.count() == 1
    assert cupons[0].user.id == response.wsgi_request.user.id
    assert cupons[0].code == "DISCOUNT20"
