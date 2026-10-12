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
