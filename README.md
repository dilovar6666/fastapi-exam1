# FastAPI Online Store

Educational REST API for an online store. It uses FastAPI, SQLAlchemy and SQLite.

## Run locally

Create a virtual environment, install dependencies and start the server:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` to use the interactive API documentation.

## Main features

The API provides users, categories and products; product filters, sorting and
pagination; carts and orders; stock updates and order cancellation; purchase
history and statistics; reviews, ratings and favorites.

## API overview

All request and response bodies use JSON. Interactive documentation is
available at `/docs`; OpenAPI is available at `/openapi.json`.

- Users support CRUD, cart, orders, purchase history and personal statistics.
- Categories support CRUD, search and product lists.
- Products support CRUD, search, price/category/stock filters, sorting and
  pagination. Catalogue selections include cheap, expensive, out-of-stock,
  low-stock, highly rated, low-rated and similar products.
- Cart items support add, update with `set`, `increase` or `decrease`, remove,
  clear and total operations.
- Orders are created from a non-empty cart, decrease stock, can be listed by
  status and can be cancelled to restore stock.
- Reviews provide ratings and comments; favorites provide a per-user product
  list.
