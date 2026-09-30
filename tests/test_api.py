import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models

# Base de datos SQLite en memoria para pruebas automáticas
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Insertar producto de prueba
    db.add(models.Product(name="Pechuga Test", category="carnes", price=4.50, stock=5, image_url="http://test.com/img.jpg"))
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def test_user_flow_and_order():
    # 1. Registro
    reg_res = client.post("/api/auth/register", json={"username": "cliente1", "password": "password123"})
    assert reg_res.status_code == 201
    assert reg_res.json()["username"] == "cliente1"

    # 2. Login
    login_res = client.post("/api/auth/login", data={"username": "cliente1", "password": "password123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Listar productos y verificar búsqueda
    prod_res = client.get("/api/products/?search=Pechuga")
    assert prod_res.status_code == 200
    prods = prod_res.json()
    assert len(prods) == 1
    prod_id = prods[0]["id"]

    # 4. Crear Orden con éxito
    order_res = client.post("/api/orders/", headers=headers, json={"items": [{"product_id": prod_id, "quantity": 2}]})
    assert order_res.status_code == 201
    assert order_res.json()["total"] == 9.0

    # 5. Probar validación de stock insuficiente (quedan 3 en stock, pedimos 4)
    fail_res = client.post("/api/orders/", headers=headers, json={"items": [{"product_id": prod_id, "quantity": 4}]})
    assert fail_res.status_code == 400
    assert "Stock insuficiente" in fail_res.json()["detail"]