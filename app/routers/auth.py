from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import re
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    pwd = user_data.password.strip()
    if len(pwd) != 6 or not pwd.isdigit():
        raise HTTPException(status_code=400, detail="La contraseña debe tener exactamente 6 dígitos numéricos.")

    user_exists = db.query(models.User).filter(models.User.username == user_data.username.strip().lower()).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado.")
    
    new_user = models.User(
        username=user_data.username.strip().lower(),
        password_hash=auth.hash_password(pwd),
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

    # Si es admin de fábrica se le permite su clave admin123, pero para usuarios estándar se valida
    user = db.query(models.User).filter(models.User.username == u).first()
    if not user or not auth.verify_password(p, user.password_hash):
        return {"success": False, "detail": "Usuario o contraseña incorrectos."}
    
    token = auth.create_access_token(data={"sub": user.username})
    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "is_admin": bool(user.is_admin),
        "username": user.username
    }

@router.get("/me", response_model=schemas.UserResponse)
def get_my_profile(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.put("/change-password")
def change_password(
    data: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not auth.verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta.")
    
    new_p = data.new_password.strip()
    if len(new_p) != 6 or not new_p.isdigit():
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener exactamente 6 dígitos numéricos.")
    
    current_user.password_hash = auth.hash_password(new_p)
    db.commit()
    return {"success": True, "message": "Contraseña actualizada exitosamente."}