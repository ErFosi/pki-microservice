"""
Esquemas Pydantic para validación de datos
"""
from pydantic import BaseModel, Field
from datetime import datetime


class CACreate(BaseModel):
    """Schema para crear una CA"""
    common_name: str = Field(..., min_length=1, max_length=255, description="Nombre común de la CA")


class CAResponse(BaseModel):
    """Schema para respuesta de CA"""
    id: int
    common_name: str
    certificate_pem: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class EncryptionTestRequest(BaseModel):
    """Schema para probar cifrado"""
    text: str = Field(..., description="Texto a cifrar")


class EncryptionTestResponse(BaseModel):
    """Schema para respuesta de prueba de cifrado"""
    original: str
    encrypted_hex: str
    decrypted: str
    match: bool
