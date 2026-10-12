def test_user_crud(client):
    created = client.post(
        "/users/", json={"name": "Alice", "email": "alice@example.com"}
    )
    assert created.status_code == 201
    user = created.json()

    fetched = client.get(f"/users/{user['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["email"] == "alice@example.com"

    updated = client.put(
        f"/users/{user['id']}",
        json={"name": "Alice Cooper", "email": "alice@example.com"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Alice Cooper"

    deleted = client.delete(f"/users/{user['id']}")
    assert deleted.status_code == 200
    assert client.get(f"/users/{user['id']}").status_code == 404
