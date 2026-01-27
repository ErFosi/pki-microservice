"""
Esquemas Pydantic para validación de datos
"""
from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Schema para login"""
    username: str = Field(..., min_length=1, description="Nombre de usuario")
    password: str = Field(..., min_length=1, description="Contraseña")


class Token(BaseModel):
    """Schema para respuesta de token"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema para datos del token"""
    username: Optional[str] = None
