from sqlalchemy.orm import Session

from model import CartItem, Category, Favorite, Order, OrderItem, Product, Review, User


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_users(db: Session):
    return db.query(User).order_by(User.id).all()


def create_user(db: Session, user):
    new_user = User(name=user.name, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user(db: Session, db_user: User, user):
    if user.name is not None:
        db_user.name = user.name
    if user.email is not None:
        db_user.email = user.email
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user: User):
    db.delete(user)
    db.commit()


def get_category(db: Session, category_id: int):
    return db.query(Category).filter(Category.id == category_id).first()


def get_categories(db: Session, search: str = None, sort_by_name: bool = False):
    query = db.query(Category)
    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))
    if sort_by_name:
        query = query.order_by(Category.name)
    else:
        query = query.order_by(Category.id)
    return query.all()


def create_category(db: Session, category):
    new_category = Category(name=category.name, description=category.description)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


def update_category(db: Session, db_category: Category, category):
    if category.name is not None:
        db_category.name = category.name
    if category.description is not None:
        db_category.description = category.description
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category: Category):
    db.delete(category)
    db.commit()


def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()


def get_products(
    db: Session,
    search: str = None,
    category_id: int = None,
    min_price: float = None,
    max_price: float = None,
    in_stock: bool = None,
    sort_by: str = None,
    descending: bool = False,
    skip: int = 0,
    limit: int = 20,
):
    query = db.query(Product)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if in_stock is True:
        query = query.filter(Product.stock > 0)
    if in_stock is False:
        query = query.filter(Product.stock == 0)

    fields = {"price": Product.price, "name": Product.name, "stock": Product.stock}
    field = fields.get(sort_by, Product.id)
    if descending:
        query = query.order_by(field.desc())
    else:
        query = query.order_by(field)
    return query.offset(skip).limit(limit).all()


def create_product(db: Session, product):
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


def update_product(db: Session, db_product: Product, product):
    if product.name is not None:
        db_product.name = product.name
    if product.description is not None:
        db_product.description = product.description
    if product.price is not None:
        db_product.price = product.price
    if product.stock is not None:
        db_product.stock = product.stock
    if product.category_id is not None:
        db_product.category_id = product.category_id
    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product: Product):
    db.delete(product)
    db.commit()


def get_cart_items(db: Session, user_id: int):
    return db.query(CartItem).filter(CartItem.user_id == user_id).order_by(CartItem.id).all()


def get_cart_item(db: Session, cart_item_id: int):
    return db.query(CartItem).filter(CartItem.id == cart_item_id).first()


def add_to_cart(db: Session, user_id: int, product: Product, quantity: int):
    cart_item = (
        db.query(CartItem).filter(CartItem.user_id == user_id, CartItem.product_id == product.id).first())
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=product.id, quantity=quantity)
        db.add(cart_item)

    db.commit()
    db.refresh(cart_item)
    return cart_item


def update_cart_item(db: Session, cart_item: CartItem, quantity: int, operation: str):
    if operation == "increase":
        cart_item.quantity += quantity

    elif operation == "decrease":
        cart_item.quantity -= quantity

    else:
        cart_item.quantity = quantity
    if cart_item.quantity < 1:
        return None
    
    db.commit()
    db.refresh(cart_item)
    return cart_item


def delete_cart_item(db: Session, cart_item: CartItem):
    db.delete(cart_item)
    db.commit()


def clear_cart(db: Session, user_id: int):
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()


def get_order(db: Session, order_id: int):
    return db.query(Order).filter(Order.id == order_id).first()


def get_orders(
    db: Session,
    status: str = None,
    sort_by: str = "date",
    descending: bool = True,
    skip: int = 0,
    limit: int = 20,
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    field = Order.total_amount if sort_by == "amount" else Order.created_at
    if descending:
        query = query.order_by(field.desc())
    else:
        query = query.order_by(field)
    return query.offset(skip).limit(limit).all()


def get_user_orders(db: Session, user_id: int):
    return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()


def get_order_total(cart_items):
    total_amount = 0
    for item in cart_items:
        if item.product.stock < item.quantity:
            return None, f"Not enough stock for product {item.product.name}"
        total_amount += item.product.price * item.quantity
    return total_amount, None


def add_order_items(db: Session, order: Order, cart_items):
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price,
        )
        db.add(order_item)
        item.product.stock -= item.quantity
        db.delete(item)


def create_order_from_cart(db: Session, user_id: int):
    cart_items = get_cart_items(db, user_id)
    if not cart_items:
        return None, "Cart is empty"

    total_amount, error = get_order_total(cart_items)
    if error:
        return None, error

    try:
        new_order = Order(user_id=user_id, total_amount=total_amount, status="new")
        db.add(new_order)
        db.flush()
        add_order_items(db, new_order, cart_items)
        db.commit()
        db.refresh(new_order)
        return new_order, None
    except Exception:
        db.rollback()
        raise


def cancel_order(db: Session, order: Order):
    if order.status == "cancelled":
        return order
    for item in order.items:
        product = get_product(db, item.product_id)
        if product:
            product.stock += item.quantity
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return order


def get_reviews(db: Session, product_id: int):
    return db.query(Review).filter(Review.product_id == product_id).order_by(Review.created_at.desc()).all()


def create_review(db: Session, product_id: int, review):
    new_review = Review(product_id=product_id, **review.model_dump())
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review


def get_review(db: Session, review_id: int):
    return db.query(Review).filter(Review.id == review_id).first()


def delete_review(db: Session, review: Review):
    db.delete(review)
    db.commit()


def get_favorite(db: Session, user_id: int, product_id: int):
    return db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.product_id == product_id).first()


def get_favorites(db: Session, user_id: int):
    return db.query(Favorite).filter(Favorite.user_id == user_id).all()


def create_favorite(db: Session, favorite):
    new_favorite = Favorite(**favorite.model_dump())
    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)
    return new_favorite


def delete_favorite(db: Session, favorite: Favorite):
    db.delete(favorite)
    db.commit()


def get_product_average_rating(db: Session, product_id: int):
    reviews = get_reviews(db, product_id)
    if not reviews:
        return 0
    total_rating = 0
    for review in reviews:
        total_rating += review.rating
    return total_rating / len(reviews)
