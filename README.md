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
