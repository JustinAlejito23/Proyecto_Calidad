from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import unicodedata
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/api/products", tags=["Productos"])

# Diccionario de palabras clave permitidas por categoría
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
    """Elimina tildes y convierte a minúsculas para comparar limpiamente."""
    text = text.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def validate_category_content(name: str, category: str):
    cat = clean_text(category)
    if cat not in ALLOWED_KEYWORDS:
        raise HTTPException(
            status_code=400, 
            detail="Categoría inválida. Solo se permite: aseo, carnes o vegetales."
        )

    clean_name = clean_text(name)
    keywords = ALLOWED_KEYWORDS[cat]

    # Verificar si el nombre contiene alguna de las palabras clave permitidas
    if not any(kw in clean_name for kw in keywords):
        raise HTTPException(
            status_code=400,
            detail=f"'{name}' no corresponde a la categoría '{category.upper()}'. Solo se permiten productos reales de este rubro."
        )

@router.get("/", response_model=List[schemas.ProductOut])
def get_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)

    if category and category.strip() != "":
        cat_clean = category.strip().lower()
        query = query.filter(func.lower(models.Product.category) == cat_clean)

    if search and search.strip() != "":
        s_clean = search.strip()
        query = query.filter(models.Product.name.ilike(f"%{s_clean}%"))

    return query.all()

# Endpoint para que el ADMIN agregue productos (con validación estricta)
@router.post("/", response_model=schemas.ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    prod_data: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado: solo el administrador puede añadir productos.")

    # Validar que el nombre corresponda a la categoría
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

# Endpoint para que el ADMIN ELIMINE productos
@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado: solo el administrador puede eliminar productos.")

    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="El producto no existe.")

    # Verificar si está en pedidos para evitar violar llaves foráneas
    order_item = db.query(models.OrderItem).filter(models.OrderItem.product_id == product_id).first()
    if order_item:
        # Si ya fue comprado, se coloca stock en 0 para no romper historiales de pedidos
        product.stock = 0
        db.commit()
        return {"message": "El producto tiene compras asociadas; su stock se colocó en 0."}

    db.delete(product)
    db.commit()
    return {"message": f"Producto '{product.name}' eliminado exitosamente."}