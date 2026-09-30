from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, description="La contraseña debe tener mínimo 6 caracteres")

class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    is_admin: bool
    username: str

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

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    items: List[OrderItemIn]

class OrderItemOut(BaseModel):
    product_id: int
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