from pydantic import BaseModel, ConfigDict, Field


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(Schema):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )


class UserUpdate(Schema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(
        default=None,
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )


class CategoryCreate(Schema):
    name: str
    description: str = None


class CategoryUpdate(Schema):
    name: str = None
    description: str = None


class ProductCreate(Schema):
    name: str
    description: str = None
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    category_id: int


class ProductUpdate(Schema):
    name: str = None
    description: str = None
    price: float = Field(default=None, gt=0)
    stock: int = Field(default=None, ge=0)
    category_id: int = None


class CartItemCreate(Schema):
    user_id: int
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(Schema):
    quantity: int = Field(ge=1)
    operation: str = "set"


class OrderCreate(Schema):
    user_id: int


class OrderStatusUpdate(Schema):
    status: str


class ReviewCreate(Schema):
    user_id: int
    rating: int = Field(ge=1, le=5)
    comment: str = None


class FavoriteCreate(Schema):
    user_id: int
    product_id: int
