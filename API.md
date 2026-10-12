# API reference

The server runs at `http://127.0.0.1:8000`. Interactive documentation is
available at `/docs`.

All request and response bodies use JSON. Successful creation requests return
`201`; a missing resource returns `404`; invalid request data returns `422`;
and a business-rule violation returns `400`.

## Users

- `POST /users/` creates a user with `name` and a unique `email`.
- `GET /users/` lists users; `GET /users/{user_id}` returns one user.
- `PUT /users/{user_id}` updates the supplied name or email.
- `DELETE /users/{user_id}` removes a user.

User-specific related data is available through:

- `GET /users/{user_id}/cart/`
- `GET /users/{user_id}/orders/`
- `GET /users/{user_id}/purchases/`
- `GET /users/{user_id}/purchases/products/{product_id}`
- `GET /users/{user_id}/statistics/`

## Categories

- `POST /categories/` creates a named category with an optional description.
- `GET /categories/` supports `search` and `sort_by_name`.
- `GET`, `PUT`, and `DELETE /categories/{category_id}` manage one category.
- `GET /categories/{category_id}/products/` lists the category catalogue.

## Products

- `POST /products/` creates a product in an existing category.
- `GET /products/{product_id}` returns one product.
- `PUT /products/{product_id}` changes supplied product fields.
- `DELETE /products/{product_id}` removes a product that is not in an order.

`GET /products/` accepts `search`, `category_id`, `min_price`, `max_price`,
`in_stock`, `sort_by`, `descending`, `skip`, and `limit`. Sorting fields are
`price`, `name`, and `stock`; pagination starts at `skip=0`.

Catalogue selections are available at `/products/cheap/`,
`/products/expensive/`, `/products/out-of-stock/`, `/products/low-stock/`,
`/products/high-rating/`, `/products/low-rating/`, and
`/products/{product_id}/similar/`.

## Cart

Use `POST /cart/add/` with `user_id`, `product_id`, and `quantity` to add an
available product. `GET /cart/{user_id}` returns cart items with each subtotal
and the cart `total_amount`.
