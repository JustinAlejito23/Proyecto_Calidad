from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ----------------------------------------------------
# 1. ESQUEMAS DE AUTENTICACIÓN (EXACTAMENTE 6 DÍGITOS)
# ----------------------------------------------------
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="Exactamente 6 dígitos numéricos")

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="Exactamente 6 dígitos numéricos")

class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    is_admin: bool
    username: str

# ----------------------------------------------------
# 2. ESQUEMAS DE PRODUCTOS
# ----------------------------------------------------
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    category: str = Field(..., min_length=3, max_length=50)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    image_url: str = Field(..., min_length=5)

class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    price: float
    stock: int
    image_url: str

    class Config:
        from_attributes = True

# ----------------------------------------------------
# 3. ESQUEMAS DE PEDIDOS Y FACTURACIÓN
# ----------------------------------------------------
class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    items: List[OrderItemIn]

class OrderItemOut(BaseModel):
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    total: float
    created_at: datetime
    items: List[OrderItemOut]

    class Config:
        from_attributes = True

# ----------------------------------------------------
# 4. ESQUEMAS DE REPORTES PARA EL ADMINISTRADOR
# ----------------------------------------------------
class OrderReportOut(BaseModel):
    id: int
    username: str
    total: float
    created_at: datetime
    item_count: int

    class Config:
        from_attributes = True

class AdminReportSummary(BaseModel):
    total_sales: float
    total_orders: int
    total_products: int
    orders: List[OrderReportOut]