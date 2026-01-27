"""
Esquemas Pydantic para validación de datos
"""
from pydantic import BaseModel, Field
from datetime import datetime


class CACreateRequest(BaseModel):
    """Schema para crear una CA"""
    common_name: str = Field(..., min_length=1, max_length=255, description="Nombre común de la CA")


class CACreateResponse(BaseModel):
    """Schema para respuesta de creación de CA"""
    crt: str = Field(..., description="Certificado de la CA en formato PEM")


class CAResponse(BaseModel):
    """Schema para respuesta de CA completa"""
    id: int
    common_name: str
    certificate_pem: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CSRSignRequest(BaseModel):
    """Schema para firmar un CSR"""
    csr: str = Field(..., description="Certificate Signing Request en formato PEM")


class CSRSignResponse(BaseModel):
    """Schema para respuesta de CSR firmado"""
    crt: str = Field(..., description="Certificado firmado en formato PEM")


class CertificateValidateRequest(BaseModel):
    """Schema para validar un certificado"""
    crt: str = Field(..., description="Certificado en formato PEM a validar")


class CertificateValidateResponse(BaseModel):
    """Schema para respuesta de validación"""
    valid: bool = Field(..., description="Si el certificado es válido")
    reason: str = Field(default="", description="Razón si no es válido")


class CertificateRevokeRequest(BaseModel):
    """Schema para revocar un certificado"""
    reason: str = Field(default="", description="Razón de la revocación")


class CertificateRevokeResponse(BaseModel):
    """Schema para respuesta de revocación"""
    success: bool
    message: str


class EncryptionTestRequest(BaseModel):
    """Schema para probar cifrado"""
    text: str = Field(..., description="Texto a cifrar")


class EncryptionTestResponse(BaseModel):
    """Schema para respuesta de prueba de cifrado"""
    original: str
    encrypted_hex: str
    decrypted: str
    match: bool
