from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    # Validación estricta en backend: mínimo 6 caracteres
    if not user_data.password or len(user_data.password.strip()) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener mínimo 6 caracteres.")

    user_exists = db.query(models.User).filter(models.User.username == user_data.username.strip().lower()).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado.")
    
    new_user = models.User(
        username=user_data.username.strip().lower(),
        password_hash=auth.hash_password(user_data.password.strip()),
        is_admin=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "success": True}

@router.post("/login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    u = credentials.username.strip().lower()
    p = credentials.password.strip()

    # Validación de longitud mínima antes de consultar
    if len(p) < 6:
        return {"success": False, "detail": "La contraseña debe tener mínimo 6 dígitos."}

    user = db.query(models.User).filter(models.User.username == u).first()
    if not user or not auth.verify_password(p, user.password_hash):
        # Retorna 200 con success: False para no generar error 401 rojo en la consola del navegador
        return {"success": False, "detail": "Usuario o contraseña incorrectos."}
    
    token = auth.create_access_token(data={"sub": user.username})
    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "is_admin": bool(user.is_admin),
        "username": user.username
    }