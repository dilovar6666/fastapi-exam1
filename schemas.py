from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class UserCreate(Schema):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=255)


class UserUpdate(Schema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, min_length=5, max_length=255)


class CategoryCreate(Schema):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class CategoryUpdate(Schema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class ProductCreate(Schema):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    category_id: int


class ProductUpdate(Schema):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    price: float = Field(default=None, gt=0)
    stock: int = Field(default=None, ge=0)
    category_id: int = None


class CartItemCreate(Schema):
    user_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(Schema):
    quantity: int = Field(ge=1)
    operation: Literal["set", "increase", "decrease"] = "set"


class OrderCreate(Schema):
    user_id: int = Field(gt=0)


class OrderStatusUpdate(Schema):
    status: Literal["new", "paid", "cancelled"]


class ReviewCreate(Schema):
    user_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class FavoriteCreate(Schema):
    user_id: int = Field(gt=0)
    product_id: int = Field(gt=0)


class UserResponse(Schema):
    id: int
    name: str
    email: str


class CategoryResponse(Schema):
    id: int
    name: str
    description: str | None


class ProductResponse(Schema):
    id: int
    name: str
    description: str | None
    price: float
    stock: int
    category_id: int


class CartItemResponse(Schema):
    id: int
    product_id: int
    quantity: int
    subtotal: float
    product: ProductResponse


class CartResponse(Schema):
    user_id: int
    items: list[CartItemResponse]
    total_amount: float


class OrderItemResponse(Schema):
    id: int
    product_id: int
    quantity: int
    price: float
    subtotal: float
    product: ProductResponse | None


class OrderResponse(Schema):
    id: int
    user_id: int
    status: str
    total_amount: float
    created_at: datetime
    items: list[OrderItemResponse]
