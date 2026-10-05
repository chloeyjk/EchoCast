def _register_and_login(client, username="chloe", password="pw12345"):
    client.post("/register", json={"username": username, "password": password})
    resp = client.post("/token", data={"username": username, "password": password})
    return resp.json()["access_token"]


def test_register_creates_user(client):
    resp = client.post("/register", json={"username": "chloe", "password": "pw12345"})

    assert resp.status_code == 200
    assert resp.json()["username"] == "chloe"


def test_register_rejects_duplicate_username(client):
    client.post("/register", json={"username": "chloe", "password": "pw12345"})

    resp = client.post("/register", json={"username": "chloe", "password": "other"})

    assert resp.status_code == 400


def test_login_returns_bearer_token(client):
    token = _register_and_login(client)

    assert token


def test_login_rejects_wrong_password(client):
    client.post("/register", json={"username": "chloe", "password": "pw12345"})

    resp = client.post("/token", data={"username": "chloe", "password": "wrong"})

    assert resp.status_code == 401


def test_preferences_require_authentication(client):
    assert client.get("/preferences").status_code == 401


def test_preferences_round_trip(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/preferences", json={"topic": "technology"}, headers=headers)
    resp = client.get("/preferences", headers=headers)

    assert [p["topic"] for p in resp.json()] == ["technology"]
