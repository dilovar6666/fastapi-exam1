from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from crud import (
    add_to_cart, cancel_order, clear_cart, create_category, create_favorite,
    create_order_from_cart, create_product, create_review, create_user,
    delete_cart_item, delete_category, delete_favorite, delete_product,
    delete_review, delete_user, get_cart_item, get_cart_items, get_categories,
    get_category, get_favorite, get_favorites, get_order, get_orders,
    get_product, get_product_average_rating, get_products, get_purchased_products,
    get_review, get_reviews, get_user, get_user_orders, get_users, update_cart_item,
    update_category, update_product, update_user,
)
from database import Base, engine, get_db
from model import CartItem, Category, Order, OrderItem, Product, User
from schemas import (
    CartItemCreate, CartItemUpdate, CategoryCreate, CategoryUpdate,
    FavoriteCreate, OrderCreate, OrderStatusUpdate, ProductCreate,
    ProductResponse, ProductUpdate, ReviewCreate, ReviewResponse, UserCreate,
    UserResponse, UserUpdate, CategoryResponse,
)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Online Store")


def order_data(order):
    items = []
    for item in order.items:
        product = None
        if item.product:
            product = ProductResponse.model_validate(item.product)
        items.append(
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
                "subtotal": item.quantity * item.price,
                "product": product,
            }
        )
    return {
        "id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "created_at": order.created_at,
        "items": items,
    }


def cart_data(db: Session, user_id: int):
    items = []
    total_amount = 0
    for item in get_cart_items(db, user_id):
        subtotal = item.quantity * item.product.price
        total_amount += subtotal
        items.append(
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "subtotal": subtotal,
                "product": ProductResponse.model_validate(item.product),
            }
        )
    return {"user_id": user_id, "items": items, "total_amount": total_amount}


def get_successful_orders(orders):
    successful_orders = []
    for order in orders:
        if order.status != "cancelled":
            successful_orders.append(order)
    return successful_orders


def get_most_expensive_order(orders):
    expensive_order = None
    for order in orders:
        if expensive_order is None or order.total_amount > expensive_order.total_amount:
            expensive_order = order
    return expensive_order


def get_purchased_product_count(orders, product_id):
    quantity = 0
    for order in orders:
        if order.status != "cancelled":
            for item in order.items:
                if item.product_id == product_id:
                    quantity += item.quantity
    return quantity


def get_total_amount(orders):
    total_amount = 0
    for order in orders:
        total_amount += order.total_amount
    return total_amount


def get_existing_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_existing_category(db: Session, category_id: int):
    category = get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


def get_existing_product(db: Session, product_id: int):
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def get_existing_order(db: Session, order_id: int):
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email is already used")
    return create_user(db, user)


@app.get("/users/", response_model=list[UserResponse])
def read_users(db: Session = Depends(get_db)):
    return get_users(db)


@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    return get_existing_user(db, user_id)


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user_endpoint(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = get_existing_user(db, user_id)
    if user.email and user.email != db_user.email:
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email is already used")
    return update_user(db, db_user, user)


@app.delete("/users/{user_id}")
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    user = get_existing_user(db, user_id)
    delete_user(db, user)
    return {"message": "User deleted"}


@app.get("/users/{user_id}/cart/")
def read_user_cart(user_id: int, db: Session = Depends(get_db)):
    get_existing_user(db, user_id)
    return cart_data(db, user_id)


@app.get("/users/{user_id}/orders/")
def read_user_orders(user_id: int, db: Session = Depends(get_db)):
    get_existing_user(db, user_id)
    return [order_data(order) for order in get_user_orders(db, user_id)]


@app.get("/users/{user_id}/purchases/")
def read_purchase_history(user_id: int, db: Session = Depends(get_db)):
    get_existing_user(db, user_id)
    orders = get_user_orders(db, user_id)
    successful_orders = get_successful_orders(orders)
    last_order = orders[0] if orders else None
    expensive_order = get_most_expensive_order(successful_orders)
    return {
        "orders": [order_data(order) for order in orders],
        "last_order": order_data(last_order) if last_order else None,
        "most_expensive_order": order_data(expensive_order) if expensive_order else None,
        "total_amount": get_total_amount(successful_orders),
        "order_count": len(successful_orders),
        "purchased_products": [
            {
                "product_id": product.id,
                "product": ProductResponse.model_validate(product),
                "quantity": quantity,
            }
            for product, quantity in get_purchased_products(db, user_id)
        ],
    }


@app.get("/users/{user_id}/purchases/products/{product_id}")
def read_purchased_product_count(user_id: int, product_id: int, db: Session = Depends(get_db)):
    get_existing_user(db, user_id)
    orders = get_user_orders(db, user_id)
    quantity = get_purchased_product_count(orders, product_id)
    return {"user_id": user_id, "product_id": product_id, "purchased_quantity": quantity}


@app.get("/users/{user_id}/statistics/")
def read_user_statistics(user_id: int, db: Session = Depends(get_db)):
    get_existing_user(db, user_id)
    orders = db.query(Order).filter(Order.user_id == user_id, Order.status != "cancelled").all()
    total_amount = get_total_amount(orders)
    return {
        "user_id": user_id,
        "order_count": len(orders),
        "total_amount": total_amount,
        "average_order_amount": total_amount / len(orders) if orders else 0,
    }


@app.post("/categories/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category_endpoint(category: CategoryCreate, db: Session = Depends(get_db)):
    if db.query(Category).filter(Category.name == category.name).first():
        raise HTTPException(status_code=400, detail="Category name is already used")
    return create_category(db, category)


@app.get("/categories/", response_model=list[CategoryResponse])
def read_categories(
    search: str = None,
    sort_by_name: bool = False,
    db: Session = Depends(get_db),
):
    return get_categories(db, search, sort_by_name)


@app.get("/categories/{category_id}", response_model=CategoryResponse)
def read_category(category_id: int, db: Session = Depends(get_db)):
    return get_existing_category(db, category_id)


@app.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category_endpoint(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db)):
    db_category = get_existing_category(db, category_id)
    if category.name and category.name != db_category.name:
        if db.query(Category).filter(Category.name == category.name).first():
            raise HTTPException(status_code=400, detail="Category name is already used")
    return update_category(db, db_category, category)


@app.delete("/categories/{category_id}")
def delete_category_endpoint(category_id: int, db: Session = Depends(get_db)):
    category = get_existing_category(db, category_id)
    if db.query(Product).filter(Product.category_id == category_id).first():
        raise HTTPException(status_code=400, detail="Category has products")
    delete_category(db, category)
    return {"message": "Category deleted"}


@app.get("/categories/{category_id}/products/")
def read_category_products(category_id: int, db: Session = Depends(get_db)):
    get_existing_category(db, category_id)
    return get_products(db, category_id=category_id, limit=100)


@app.post("/products/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product_endpoint(product: ProductCreate, db: Session = Depends(get_db)):
    get_existing_category(db, product.category_id)
    return create_product(db, product)


@app.get("/products/", response_model=list[ProductResponse])
def read_products(
    search: str = None,
    category_id: int = None,
    min_price: float = Query(default=None, gt=0),
    max_price: float = Query(default=None, gt=0),
    in_stock: bool = None,
    sort_by: str = None,
    descending: bool = False,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=400, detail="Minimum price is greater than maximum price")
    
    if sort_by not in (None, "price", "name", "stock"):
        raise HTTPException(status_code=400, detail="sort_by must be price, name or stock")
    
    return get_products(db, search, category_id, min_price, max_price, in_stock, sort_by, descending, skip, limit)


@app.get("/products/cheap/")
def read_cheap_products(limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    return get_products(db, sort_by="price", limit=limit)


@app.get("/products/expensive/")
def read_expensive_products(limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    return get_products(db, sort_by="price", descending=True, limit=limit)


@app.get("/products/out-of-stock/")
def read_out_of_stock_products(db: Session = Depends(get_db)):
    return get_products(db, in_stock=False, limit=100)


@app.get("/products/low-stock/")
def read_low_stock_products(db: Session = Depends(get_db)):
    return db.query(Product).filter(Product.stock < 5).order_by(Product.stock).all()


@app.get("/products/high-rating/")
def read_high_rating_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    high_rating_products = []
    for product in products:
        average_rating = get_product_average_rating(db, product.id)
        if average_rating >= 4:
            high_rating_products.append({"product": ProductResponse.model_validate(product), "average_rating": average_rating})
    return high_rating_products


@app.get("/products/low-rating/")
def read_low_rating_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    low_rating_products = []
    for product in products:
        reviews = get_reviews(db, product.id)
        if reviews:
            average_rating = get_product_average_rating(db, product.id)
            if average_rating <= 2:
                low_rating_products.append({"product": ProductResponse.model_validate(product), "average_rating": average_rating})
    return low_rating_products


@app.get("/products/{product_id}", response_model=ProductResponse)
def read_product(product_id: int, db: Session = Depends(get_db)):
    return get_existing_product(db, product_id)


@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product_endpoint(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    db_product = get_existing_product(db, product_id)
    if product.category_id is not None:
        get_existing_category(db, product.category_id)
    return update_product(db, db_product, product)


@app.delete("/products/{product_id}")
def delete_product_endpoint(product_id: int, db: Session = Depends(get_db)):
    product = get_existing_product(db, product_id)
    order_item = (
        db.query(OrderItem)
        .filter(OrderItem.product_id == product_id)
        .first()
    )
    if order_item:
        raise HTTPException(status_code=400, detail="Product is in an order and cannot be deleted")
    delete_product(db, product)
    return {"message": "Product deleted"}


@app.get("/products/{product_id}/similar/")
def read_similar_products(product_id: int, db: Session = Depends(get_db)):
    product = get_existing_product(db, product_id)
    return (
        db.query(Product)
        .filter(Product.category_id == product.category_id, Product.id != product.id)
        .order_by(Product.id)
        .limit(10)
        .all()
    )


@app.post("/cart/add/", status_code=status.HTTP_201_CREATED)
def add_to_cart_endpoint(item: CartItemCreate, db: Session = Depends(get_db)):
    get_existing_user(db, item.user_id)
    product = get_existing_product(db, item.product_id)
    if product.stock == 0:
        raise HTTPException(status_code=400, detail="Product is out of stock")
    current_item = (
        db.query(CartItem)
        .filter(CartItem.user_id == item.user_id, CartItem.product_id == item.product_id)
        .first()
    )
    current_quantity = current_item.quantity if current_item else 0
    if current_quantity + item.quantity > product.stock:
        raise HTTPException(status_code=400, detail="Quantity is greater than stock")
    return add_to_cart(db, item.user_id, product, item.quantity)


@app.get("/cart/{user_id}")
def read_cart(user_id: int, db: Session = Depends(get_db)):
    get_existing_user(db, user_id)
    return cart_data(db, user_id)


@app.get("/cart/{user_id}/total/")
def read_cart_total(user_id: int, db: Session = Depends(get_db)):
    get_existing_user(db, user_id)
    return {"user_id": user_id, "total_amount": cart_data(db, user_id)["total_amount"]}


@app.patch("/cart/items/{cart_item_id}")
def update_cart_item_endpoint(cart_item_id: int, item: CartItemUpdate, db: Session = Depends(get_db)):
    cart_item = get_cart_item(db, cart_item_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if item.operation not in ("set", "increase", "decrease"):
        raise HTTPException(status_code=400, detail="operation must be set, increase or decrease")
    if item.operation == "increase" and cart_item.quantity + item.quantity > cart_item.product.stock:
        raise HTTPException(status_code=400, detail="Quantity is greater than stock")
    if item.operation == "set" and item.quantity > cart_item.product.stock:
        raise HTTPException(status_code=400, detail="Quantity is greater than stock")
    if item.operation == "decrease" and cart_item.quantity - item.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity cannot be less than 1")
    updated_item = update_cart_item(db, cart_item, item.quantity, item.operation)
    if not updated_item:
        raise HTTPException(status_code=400, detail="Quantity cannot be less than 1")
    return updated_item


@app.delete("/cart/items/{cart_item_id}")
def delete_cart_item_endpoint(cart_item_id: int, db: Session = Depends(get_db)):
    cart_item = get_cart_item(db, cart_item_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    delete_cart_item(db, cart_item)
    return {"message": "Cart item deleted"}


@app.delete("/cart/clear/{user_id}")
def clear_cart_endpoint(user_id: int, db: Session = Depends(get_db)):
    get_existing_user(db, user_id)
    clear_cart(db, user_id)
    return {"message": "Cart cleared"}


@app.post("/orders/create/", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    get_existing_user(db, order.user_id)
    new_order, error = create_order_from_cart(db, order.user_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return order_data(get_order(db, new_order.id))


@app.get("/orders/")
def read_orders(
    status: Literal["new", "paid", "cancelled"] | None = None,
    sort_by: str = "date",
    descending: bool = True,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if status not in (None, "new", "paid", "cancelled"):
        raise HTTPException(status_code=400, detail="status must be new, paid or cancelled")
    if sort_by not in ("date", "amount"):
        raise HTTPException(status_code=400, detail="sort_by must be date or amount")
    return [order_data(order) for order in get_orders(db, status, sort_by, descending, skip, limit)]


@app.get("/orders/new/")
def read_new_orders(db: Session = Depends(get_db)):
    return [order_data(order) for order in get_orders(db, status="new")]


@app.get("/orders/paid/")
def read_paid_orders(db: Session = Depends(get_db)):
    return [order_data(order) for order in get_orders(db, status="paid")]


@app.get("/orders/cancelled/")
def read_cancelled_orders(db: Session = Depends(get_db)):
    return [order_data(order) for order in get_orders(db, status="cancelled")]


@app.get("/orders/{order_id}")
def read_order(order_id: int, db: Session = Depends(get_db)):
    return order_data(get_existing_order(db, order_id))


@app.patch("/orders/{order_id}/status/")
def update_order_status(order_id: int, order_status: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = get_existing_order(db, order_id)
    if order_status.status not in ("new", "paid", "cancelled"):
        raise HTTPException(status_code=400, detail="Status must be new, paid or cancelled")
    if order_status.status == "cancelled":
        return order_data(cancel_order(db, order))
    if order.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cancelled order cannot be changed")
    order.status = order_status.status
    db.commit()
    db.refresh(order)
    return order_data(order)


@app.post("/orders/{order_id}/cancel/")
def cancel_order_endpoint(order_id: int, db: Session = Depends(get_db)):
    order = get_existing_order(db, order_id)
    return order_data(cancel_order(db, order))


@app.post("/products/{product_id}/reviews/", status_code=status.HTTP_201_CREATED)
def create_review_endpoint(product_id: int, review: ReviewCreate, db: Session = Depends(get_db)):
    get_existing_product(db, product_id)
    get_existing_user(db, review.user_id)
    return create_review(db, product_id, review)


@app.get("/products/{product_id}/reviews/")
def read_reviews(product_id: int, db: Session = Depends(get_db)):
    get_existing_product(db, product_id)
    return get_reviews(db, product_id)


@app.get("/products/{product_id}/rating/")
def read_product_rating(product_id: int, db: Session = Depends(get_db)):
    get_existing_product(db, product_id)
    average_rating = get_product_average_rating(db, product_id)
    return {"product_id": product_id, "average_rating": average_rating or 0}


@app.delete("/reviews/{review_id}")
def delete_review_endpoint(review_id: int, db: Session = Depends(get_db)):
    review = get_review(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    delete_review(db, review)
    return {"message": "Review deleted"}


@app.post("/favorites/", status_code=status.HTTP_201_CREATED)
def create_favorite_endpoint(favorite: FavoriteCreate, db: Session = Depends(get_db)):
    get_existing_user(db, favorite.user_id)
    get_existing_product(db, favorite.product_id)
    if get_favorite(db, favorite.user_id, favorite.product_id):
        raise HTTPException(status_code=400, detail="Product is already in favorites")
    return create_favorite(db, favorite)


@app.get("/favorites/")
def read_favorites(user_id: int, db: Session = Depends(get_db)):
    get_existing_user(db, user_id)
    return [ProductResponse.model_validate(favorite.product) for favorite in get_favorites(db, user_id)]


@app.get("/favorites/{user_id}/{product_id}")
def read_favorite(user_id: int, product_id: int, db: Session = Depends(get_db)):
    get_existing_user(db, user_id)
    get_existing_product(db, product_id)
    favorite = get_favorite(db, user_id, product_id)
    return {"in_favorites": favorite is not None}


@app.delete("/favorites/{user_id}/{product_id}")
def delete_favorite_endpoint(user_id: int, product_id: int, db: Session = Depends(get_db)):
    favorite = get_favorite(db, user_id, product_id)
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    delete_favorite(db, favorite)
    return {"message": "Product removed from favorites"}


@app.get("/statistics/")
def read_statistics(db: Session = Depends(get_db)):
    counts = db.query(
        select(func.count(User.id)).scalar_subquery(),
        select(func.count(Product.id)).scalar_subquery(),
        select(func.count(Category.id)).scalar_subquery(),
    ).first()
    users_cnt, products_cnt, categories_cnt = counts or (0, 0, 0)

    orders_stat = (
        db.query(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_amount), 0),
            func.coalesce(func.avg(Order.total_amount), 0),
        )
        .filter(Order.status != "cancelled")
        .first()
    )
    orders_cnt, total_amount, avg_amount = orders_stat or (0, 0, 0)

    most_sold = (
        db.query(Product, func.sum(OrderItem.quantity))
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status != "cancelled")
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .first()
    )
    best_customer = (
        db.query(User, func.sum(Order.total_amount))
        .join(Order, User.id == Order.user_id)
        .filter(Order.status != "cancelled")
        .group_by(User.id)
        .order_by(func.sum(Order.total_amount).desc())
        .first()
    )

    to_pydantic = lambda obj: ProductResponse.model_validate(obj) if obj else None

    return {
        "users_count": users_cnt,
        "products_count": products_cnt,
        "categories_count": categories_cnt,
        "orders_count": orders_cnt,
        "total_orders_amount": total_amount,
        "average_order_amount": float(avg_amount),
        "most_sold_product": to_pydantic(most_sold[0]) if most_sold else None,
        "most_sold_quantity": most_sold[1] if most_sold else 0,
        "most_expensive_product": to_pydantic(db.query(Product).order_by(Product.price.desc()).first()),
        "cheapest_product": to_pydantic(db.query(Product).order_by(Product.price.asc()).first()),
        "low_stock_products": [
            ProductResponse.model_validate(product)
            for product in db.query(Product).filter(Product.stock < 5).order_by(Product.stock).all()
        ],
        "best_customer": {"id": best_customer[0].id, "name": best_customer[0].name, "total_amount": best_customer[1]} if best_customer else None,
    }
