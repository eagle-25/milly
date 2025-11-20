from django.urls import path

from commerce.adapter.web.views import (
    ProductsView,
    create_cupon_view,
    get_product_detail_view,
    update_product_stock_view,
    upsert_product_discount_view,
)

urlpatterns = [
    path("coupons/", create_cupon_view, name="create-cupon"),  # Post
    path("products/", ProductsView.as_view(), name="products"),  # Get, Post
    path(
        "products/<str:product_id>/", get_product_detail_view, name="get-product-detail"
    ),  # Get
    path(
        "products/<str:product_id>/stock/",
        update_product_stock_view,
        name="update-product-stock",
    ),  # Post
    path(
        "products/<str:product_id>/discounts/",
        upsert_product_discount_view,
        name="create-product-discount",
    ),  # Post
]
