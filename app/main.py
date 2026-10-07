from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.database import engine, Base, SessionLocal
from app import models, auth
from app.routers import auth as auth_router, products, orders

# Crear tablas en PostgreSQL si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MiniStore API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router.router)
app.include_router(products.router)
app.include_router(orders.router)

# Rutas de carpetas estáticas y subida de archivos
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
UPLOADS_DIR = os.path.join(FRONTEND_DIR, "uploads")
INDEX_PATH = os.path.join(FRONTEND_DIR, "index.html")
FAVICON_PATH = os.path.join(FRONTEND_DIR, "favicon.ico")

# Asegurar que existan las carpetas
os.makedirs(FRONTEND_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Servir archivos estáticos locales y uploads
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def read_root():
    return FileResponse(INDEX_PATH)

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    if os.path.exists(FAVICON_PATH):
        return FileResponse(FAVICON_PATH)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
def devtools_json():
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.on_event("startup")
def setup_initial_data():
    db = SessionLocal()
    try:
        # 1. Crear usuario administrador por defecto si no existe
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            admin_user = models.User(
                username="admin",
                password_hash=auth.hash_password("admin123"),
                is_admin=True
            )
            db.add(admin_user)
            db.commit()

        # 2. Cargar productos base iniciales si la tabla está vacía
        if db.query(models.Product).count() == 0:
            sample_items = [
                models.Product(name="Detergente Líquido 1L", category="aseo", price=3.50, stock=20, image_url="https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=400&q=80"),
                models.Product(name="Jabón Antibacterial 3 Pack", category="aseo", price=2.20, stock=35, image_url="https://images.unsplash.com/photo-1607006314143-6c8411b7d5ca?auto=format&fit=crop&w=400&q=80"),
                models.Product(name="Limpia Pisos Lavanda 750ml", category="aseo", price=1.80, stock=15, image_url="https://images.unsplash.com/photo-1563453392212-326f5e854473?auto=format&fit=crop&w=400&q=80"),
                models.Product(name="Pechuga de Pollo 1kg", category="carnes", price=4.20, stock=18, image_url="https://images.unsplash.com/photo-1604503468506-a8da13d82791?auto=format&fit=crop&w=400&q=80"),
                models.Product(name="Lomo de Res Fresco 1kg", category="carnes", price=7.50, stock=12, image_url="https://images.unsplash.com/photo-1558030006-450675393462?auto=format&fit=crop&w=400&q=80"),
                models.Product(name="Chuleta de Cerdo 1kg", category="carnes", price=5.10, stock=10, image_url="https://images.unsplash.com/photo-1432139555190-58524dae6a55?auto=format&fit=crop&w=400&q=80"),
                models.Product(name="Tomate Riñón 1kg", category="vegetales", price=1.10, stock=40, image_url="https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=400&q=80"),
                models.Product(name="Zanahoria Criolla 1kg", category="vegetales", price=0.85, stock=50, image_url="https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?auto=format&fit=crop&w=400&q=80"),
                models.Product(name="Lechuga Crespa x Unidad", category="vegetales", price=0.60, stock=25, image_url="https://images.unsplash.com/photo-1622206151226-18ca2c9ab4a1?auto=format&fit=crop&w=400&q=80"),
            ]
            db.add_all(sample_items)
            db.commit()
    finally:
        db.close()