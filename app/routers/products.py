from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import unicodedata
import os
import uuid
import shutil
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/api/products", tags=["Productos"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_KEYWORDS = {
    "aseo": [
        "jabon", "detergente", "cloro", "desinfectante", "escoba", "trapeador", 
        "limpiador", "suavizante", "lavavajillas", "papel higienico", "shampoo", 
        "acondicionador", "pasta dental", "esponja", "toalla", "cepillo", "fabuloso", 
        "aseo", "limpia pisos", "lejia", "blanqueador", "aromatizante", "fregona"
    ],
    "carnes": [
        "carne", "pollo", "res", "cerdo", "chuleta", "lomo", "pechuga", "costilla", 
        "molida", "salchicha", "jamon", "tocino", "pescado", "filete", "alitas", 
        "muslo", "bife", "pavo", "cordero", "chorizo", "embutido", "marisco", "camaron"
    ],
    "vegetales": [
        "tomate", "zanahoria", "lechuga", "cebolla", "papa", "patata", "pepino", 
        "pimiento", "brocoli", "espinaca", "coliflor", "aguacate", "ajo", "cilantro", 
        "perejil", "apio", "remolacha", "calabaza", "choclo", "maiz", "vainita", 
        "alverja", "arveja", "rabano", "champinon", "seta", "verdura", "vegetal"
    ]
}

def clean_text(text: str) -> str:
    text = text.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def validate_category_content(name: str, category: str):
    cat = clean_text(category)
    if cat not in ALLOWED_KEYWORDS:
        raise HTTPException(status_code=400, detail="Categoría inválida. Solo se permite: aseo, carnes o vegetales.")

    clean_name = clean_text(name)
    keywords = ALLOWED_KEYWORDS[cat]
    if not any(kw in clean_name for kw in keywords):
        raise HTTPException(
            status_code=400,
            detail=f"Validación: '{name}' no corresponde a la categoría {category.upper()}. Solo se aceptan productos válidos de esta sección."
        )

@router.get("/", response_model=List[schemas.ProductOut])
def get_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    include_out_of_stock: bool = Query(True),
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)
    if not include_out_of_stock:
        query = query.filter(models.Product.stock > 0)
    if category and category.strip() != "":
        cat_clean = category.strip().lower()
        query = query.filter(func.lower(models.Product.category) == cat_clean)
    if search and search.strip() != "":
        s_clean = search.strip()
        query = query.filter(models.Product.name.ilike(f"%{s_clean}%"))
    return query.all()

# Endpoint para subir archivo físico de imagen (REQ 4)
@router.post("/upload-image")
def upload_image(file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Solo administradores pueden subir imágenes.")
    
    file_ext = os.path.splitext(file.filename)[1]
    if file_ext.lower() not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        raise HTTPException(status_code=400, detail="Formato de imagen inválido. Use JPG, PNG o WEBP.")
    
    filename = f"{uuid.uuid4().hex}{file_ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"url": f"/static/uploads/{filename}"}

@router.post("/", response_model=schemas.ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    prod_data: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Solo el administrador puede añadir productos.")

    validate_category_content(prod_data.name, prod_data.category)

    new_prod = models.Product(
        name=prod_data.name.strip(),
        category=prod_data.category.strip().lower(),
        price=round(prod_data.price, 2),
        stock=prod_data.stock,
        image_url=prod_data.image_url.strip()
    )
    db.add(new_prod)
    db.commit()
    db.refresh(new_prod)
    return new_prod

@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado: solo administradores.")
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="El producto no existe.")

    db.query(models.OrderItem).filter(models.OrderItem.product_id == product_id).delete(synchronize_session=False)
    db.delete(product)
    db.commit()
    return {"message": f"Producto '{product.name}' eliminado permanentemente."}