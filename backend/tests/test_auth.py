def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "合同管理系统"


def test_login_fail(client):
    response = client.post("/api/v1/auth/login", json={
        "username": "nonexistent",
        "password": "wrong",
    })
    assert response.status_code == 401


def test_register_then_login(client):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.user import User
    from app.services.auth_service import hash_password

    engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    db = Session()
    admin = User(
        username="testadmin",
        password_hash=hash_password("admin123"),
        role="admin",
        department="管理部",
        display_name="测试管理员",
    )
    db.add(admin)
    db.commit()
    db.close()

    # Login as admin
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "testadmin",
        "password": "admin123",
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]

    # Register a new user
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "password": "123456",
            "role": "handler",
            "department": "测试部",
            "display_name": "测试用户",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reg_resp.status_code == 200

    # Login as new user
    login2 = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "123456",
    })
    assert login2.status_code == 200
    assert login2.json()["data"]["user"]["role"] == "handler"
