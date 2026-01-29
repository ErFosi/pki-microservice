"""
CA Service - Servicio de Autoridad Certificadora

Endpoints:
- POST /crypto/ca - Crear una CA
- POST /crypto/crt - Firmar un CSR
- POST /crypto/cert/revoke/{id} - Revocar un certificado
- POST /crypto/validate - Validar un certificado
- GET /crl - Obtener la CRL en formato PEM
- POST /test/encryption - Prueba de cifrado/descifrado (testing)
- GET /health - Health check
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
from datetime import datetime

from database import get_db, init_db
from crypto_utils import get_crypto_helper, CryptoHelper
from models import CertificateAuthority, Certificate, RevokedCertificate
from schemas import (
    EncryptionTestRequest, EncryptionTestResponse,
    CACreateRequest, CACreateResponse,
    CAResponse, CAListResponse,
    CertificateResponse, CertificateListResponse,
    CSRSignRequest, CSRSignResponse,
    CertificateValidateRequest, CertificateValidateResponse,
    CertificateRevokeRequest, CertificateRevokeResponse
)
from config import get_settings
import pki_utils

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events - Inicializa la DB al arrancar
    """
    print("🚀 Inicializando base de datos...")
    await init_db()
    print("✅ Base de datos inicializada")
    yield
    print("👋 Cerrando aplicación...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Servicio de Autoridad Certificadora con cifrado de claves privadas",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }


@app.post("/test/encryption", response_model=EncryptionTestResponse)
async def test_encryption(
    request: EncryptionTestRequest,
    crypto: CryptoHelper = Depends(get_crypto_helper)
):
    """
    Endpoint temporal para probar el cifrado/descifrado
    
    Este endpoint:
    1. Recibe un texto plano
    2. Lo cifra usando la MASTER_KEY
    3. Lo descifra
    4. Verifica que coincida con el original
    
    SOLO PARA TESTING - Eliminar en producción
    """
    try:
        # Cifrar el texto
        encrypted_bytes = crypto.encrypt_string(request.text)
        
        # Descifrar el texto
        decrypted_text = crypto.decrypt_string(encrypted_bytes)
        
        # Verificar que coincidan
        match = decrypted_text == request.text
        
        return EncryptionTestResponse(
            original=request.text,
            encrypted_hex=encrypted_bytes.hex(),  # Convertir a hex para visualización
            decrypted=decrypted_text,
            match=match
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en cifrado/descifrado: {str(e)}"
        )


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "list_cas": "GET /ca",
            "get_ca": "GET /ca/{id}",
            "create_ca": "POST /ca",
            "list_certificates": "GET /certificates",
            "get_certificate": "GET /certificates/{id}",
            "sign_csr": "POST /crt",
            "revoke_cert": "POST /cert/revoke/{id}",
            "validate_cert": "POST /validate",
            "get_crl": "GET /crl?ca_common_name={name}"
        }
    }


@app.get("/ca", response_model=list[CAListResponse])
async def list_cas(db: AsyncSession = Depends(get_db)):
    """
    Listar todas las Certificate Authorities (CAs)
    
    Returns:
        Lista de CAs con información básica
    """
    try:
        result = await db.execute(select(CertificateAuthority))
        cas = result.scalars().all()
        
        return [
            CAListResponse(
                id=ca.id,
                common_name=ca.common_name,
                created_at=ca.created_at
            )
            for ca in cas
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing CAs: {str(e)}"
        )


@app.get("/ca/{ca_id}", response_model=CAResponse)
async def get_ca(ca_id: int, db: AsyncSession = Depends(get_db)):
    """
    Obtener detalles de una CA específica
    
    Args:
        ca_id: ID de la CA
    
    Returns:
        Detalles completos de la CA incluyendo certificado
    """
    try:
        result = await db.execute(
            select(CertificateAuthority).where(CertificateAuthority.id == ca_id)
        )
        ca = result.scalar_one_or_none()
        
        if not ca:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CA with ID {ca_id} not found"
            )
        
        return CAResponse(
            id=ca.id,
            common_name=ca.common_name,
            certificate_pem=ca.certificate_pem,
            created_at=ca.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting CA: {str(e)}"
        )


@app.get("/certificates", response_model=list[CertificateListResponse])
async def list_certificates(
    ca_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Listar certificados emitidos
    
    Args:
        ca_id: Filtrar por CA específica (opcional)
        skip: Número de registros a omitir (paginación)
        limit: Número máximo de registros a devolver
    
    Returns:
        Lista de certificados
    """
    try:
        query = select(Certificate)
        
        if ca_id is not None:
            query = query.where(Certificate.ca_id == ca_id)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        certificates = result.scalars().all()
        
        return [
            CertificateListResponse(
                id=cert.id,
                serial_number=cert.serial_number,
                common_name=cert.common_name,
                ca_id=cert.ca_id,
                created_at=cert.created_at,
                expires_at=cert.expires_at
            )
            for cert in certificates
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing certificates: {str(e)}"
        )


@app.get("/certificates/{cert_id}", response_model=CertificateResponse)
async def get_certificate(cert_id: int, db: AsyncSession = Depends(get_db)):
    """
    Obtener detalles de un certificado específico
    
    Args:
        cert_id: ID del certificado
    
    Returns:
        Detalles completos del certificado incluyendo PEM
    """
    try:
        result = await db.execute(
            select(Certificate).where(Certificate.id == cert_id)
        )
        cert = result.scalar_one_or_none()
        
        if not cert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Certificate with ID {cert_id} not found"
            )
        
        return CertificateResponse(
            id=cert.id,
            serial_number=cert.serial_number,
            common_name=cert.common_name,
            certificate_pem=cert.certificate_pem,
            ca_id=cert.ca_id,
            created_at=cert.created_at,
            expires_at=cert.expires_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting certificate: {str(e)}"
        )


@app.post("/ca", response_model=CACreateResponse)
async def create_ca(
    request: CACreateRequest,
    db: AsyncSession = Depends(get_db),
    crypto: CryptoHelper = Depends(get_crypto_helper)
):
    """
    Crear una nueva Certificate Authority (CA)
    
    1. Genera una clave privada RSA
    2. Crea un certificado autofirmado
    3. Cifra la clave privada con la MASTER_KEY
    4. Guarda la CA en la base de datos
    
    Args:
        request: Debe contener el common_name de la CA
    
    Returns:
        Certificado de la CA en formato PEM
    """
    try:
        # Verificar que no exista una CA con el mismo common_name
        result = await db.execute(
            select(CertificateAuthority).where(
                CertificateAuthority.common_name == request.common_name
            )
        )
        existing_ca = result.scalar_one_or_none()
        
        if existing_ca:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"CA with common_name '{request.common_name}' already exists"
            )
        
        # 1. Generar clave privada RSA
        private_key = pki_utils.generate_private_key(key_size=2048)
        
        # 2. Generar certificado autofirmado
        certificate = pki_utils.generate_ca_certificate(
            common_name=request.common_name,
            private_key=private_key,
            validity_days=3650  # 10 años
        )
        
        # 3. Serializar a PEM
        private_key_pem = pki_utils.private_key_to_pem(private_key)
        certificate_pem = pki_utils.certificate_to_pem(certificate)
        
        # 4. Cifrar la clave privada
        encrypted_private_key = crypto.encrypt(private_key_pem)
        
        # 5. Guardar en la base de datos
        ca = CertificateAuthority(
            common_name=request.common_name,
            private_key=encrypted_private_key,
            certificate_pem=certificate_pem
        )
        db.add(ca)
        await db.commit()
        await db.refresh(ca)
        
        return CACreateResponse(crt=certificate_pem)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating CA: {str(e)}"
        )


@app.post("/crt", response_model=CSRSignResponse)
async def sign_csr(
    request: CSRSignRequest,
    db: AsyncSession = Depends(get_db),
    crypto: CryptoHelper = Depends(get_crypto_helper)
):
    """
    Firmar un Certificate Signing Request (CSR)
    
    1. Recibe un CSR en formato PEM
    2. Busca la CA especificada por common_name (o usa la primera si no se especifica)
    3. Descifra la clave privada de la CA
    4. Firma el CSR generando un certificado
    5. Guarda el certificado en la BD
    
    Args:
        request: Debe contener el CSR en formato PEM y opcionalmente el ca_common_name
    
    Returns:
        Certificado firmado en formato PEM
    """
    try:
        # 1. Parsear el CSR
        csr = pki_utils.csr_from_pem(request.csr)
        
        # 2. Obtener la CA especificada o la primera disponible
        if request.ca_common_name:
            # Buscar CA por common_name
            result = await db.execute(
                select(CertificateAuthority).where(
                    CertificateAuthority.common_name == request.ca_common_name
                )
            )
            ca = result.scalar_one_or_none()
            
            if not ca:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"CA with common_name '{request.ca_common_name}' not found"
                )
        else:
            # Usar la primera CA disponible
            result = await db.execute(select(CertificateAuthority).limit(1))
            ca = result.scalar_one_or_none()
            
            if not ca:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No CA found. Please create a CA first using POST /crypto/ca"
                )
        
        # 3. Descifrar la clave privada de la CA
        decrypted_private_key_pem = crypto.decrypt(ca.private_key)
        ca_private_key = pki_utils.private_key_from_pem(decrypted_private_key_pem)
        
        # 4. Parsear el certificado de la CA
        ca_certificate = pki_utils.certificate_from_pem(ca.certificate_pem)
        
        # 5. Firmar el CSR
        certificate = pki_utils.sign_csr(
            csr=csr,
            ca_certificate=ca_certificate,
            ca_private_key=ca_private_key,
            validity_days=365  # 1 año
        )
        
        # 6. Serializar el certificado
        certificate_pem = pki_utils.certificate_to_pem(certificate)
        
        # 7. Guardar el certificado en la BD
        cert_record = Certificate(
            serial_number=pki_utils.get_certificate_serial_number(certificate),
            common_name=pki_utils.get_certificate_common_name(certificate),
            certificate_pem=certificate_pem,
            ca_id=ca.id,
            expires_at=certificate.not_valid_after_utc
        )
        db.add(cert_record)
        await db.commit()
        
        return CSRSignResponse(crt=certificate_pem)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSR: {str(e)}"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error signing CSR: {str(e)}"
        )


@app.post("/cert/revoke/{cert_id}", response_model=CertificateRevokeResponse)
async def revoke_certificate(
    cert_id: int,
    request: CertificateRevokeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Revocar un certificado (añadir a la CRL)
    
    Args:
        cert_id: ID del certificado a revocar
        request: Razón de la revocación (opcional)
    
    Returns:
        Confirmación de la revocación
    """
    try:
        # Buscar el certificado
        result = await db.execute(
            select(Certificate).where(Certificate.id == cert_id)
        )
        cert = result.scalar_one_or_none()
        
        if not cert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Certificate with ID {cert_id} not found"
            )
        
        # Verificar si ya está revocado
        result = await db.execute(
            select(RevokedCertificate).where(
                RevokedCertificate.certificate_id == cert_id
            )
        )
        already_revoked = result.scalar_one_or_none()
        
        if already_revoked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Certificate {cert_id} is already revoked"
            )
        
        # Añadir a la CRL
        revoked = RevokedCertificate(
            certificate_id=cert_id,
            serial_number=cert.serial_number,
            reason=request.reason or "Unspecified"
        )
        db.add(revoked)
        await db.commit()
        
        return CertificateRevokeResponse(
            success=True,
            message=f"Certificate {cert_id} (serial: {cert.serial_number}) successfully revoked"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking certificate: {str(e)}"
        )


@app.post("/validate", response_model=CertificateValidateResponse)
async def validate_certificate(
    request: CertificateValidateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Validar un certificado
    
    Verifica:
    1. Firma del certificado contra la CA emisora
    2. Fechas de validez
    3. Estado de revocación (CRL)
    
    El CA emisor se determina automáticamente desde el certificado (issuer),
    pero puede especificarse manualmente con ca_common_name.
    
    Args:
        request: Certificado en formato PEM y opcionalmente ca_common_name
    
    Returns:
        valid: True/False y razón si no es válido
    """
    try:
        # 1. Parsear el certificado
        certificate = pki_utils.certificate_from_pem(request.crt)
        serial_number = pki_utils.get_certificate_serial_number(certificate)
        
        # 2. Verificar si está revocado
        result = await db.execute(
            select(RevokedCertificate).where(
                RevokedCertificate.serial_number == serial_number
            )
        )
        revoked = result.scalar_one_or_none()
        
        if revoked:
            return CertificateValidateResponse(
                valid=False,
                reason=f"Certificate is revoked: {revoked.reason}"
            )
        
        # 3. Determinar qué CA usar para validación
        if request.ca_common_name:
            # Usar la CA especificada
            result = await db.execute(
                select(CertificateAuthority).where(
                    CertificateAuthority.common_name == request.ca_common_name
                )
            )
            ca = result.scalar_one_or_none()
            
            if not ca:
                return CertificateValidateResponse(
                    valid=False,
                    reason=f"Specified CA '{request.ca_common_name}' not found"
                )
            
            cas_to_check = [ca]
        else:
            # Extraer el issuer common name del certificado
            try:
                issuer_cn = pki_utils.get_certificate_issuer_common_name(certificate)
                
                # Buscar la CA por issuer common name
                result = await db.execute(
                    select(CertificateAuthority).where(
                        CertificateAuthority.common_name == issuer_cn
                    )
                )
                ca = result.scalar_one_or_none()
                
                if ca:
                    cas_to_check = [ca]
                else:
                    # Si no encontramos la CA específica, validar contra todas
                    result = await db.execute(select(CertificateAuthority))
                    cas_to_check = result.scalars().all()
            except Exception:
                # Si no se puede extraer el issuer, validar contra todas las CAs
                result = await db.execute(select(CertificateAuthority))
                cas_to_check = result.scalars().all()
        
        if not cas_to_check:
            return CertificateValidateResponse(
                valid=False,
                reason="No CA found to validate against"
            )
        
        # 4. Intentar validar con las CAs seleccionadas
        for ca in cas_to_check:
            ca_certificate = pki_utils.certificate_from_pem(ca.certificate_pem)
            if pki_utils.validate_certificate(certificate, ca_certificate):
                return CertificateValidateResponse(
                    valid=True,
                    reason=f"Certificate is valid (issued by {ca.common_name})"
                )
        
        return CertificateValidateResponse(
            valid=False,
            reason="Certificate signature is invalid or expired"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid certificate: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating certificate: {str(e)}"
        )


@app.get("/crl", response_class=PlainTextResponse)
async def get_crl(
    ca_common_name: str,
    db: AsyncSession = Depends(get_db),
    crypto: CryptoHelper = Depends(get_crypto_helper)
):
    """
    Obtener la Certificate Revocation List (CRL) en formato PEM de una CA específica
    
    Args:
        ca_common_name: Common name de la CA que genera la CRL
    
    Returns:
        CRL en formato PEM firmada por la CA especificada
    """
    try:
        # Buscar la CA por common_name
        result = await db.execute(
            select(CertificateAuthority).where(
                CertificateAuthority.common_name == ca_common_name
            )
        )
        ca = result.scalar_one_or_none()
        
        if not ca:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CA with common_name '{ca_common_name}' not found"
            )
        
        # Obtener solo los certificados revocados emitidos por esta CA
        result = await db.execute(
            select(RevokedCertificate)
            .join(Certificate, Certificate.id == RevokedCertificate.certificate_id)
            .where(Certificate.ca_id == ca.id)
        )
        revoked_records = result.scalars().all()
        revoked_serials = [rec.serial_number for rec in revoked_records]
        
        # Parsear certificado de la CA
        ca_cert = pki_utils.certificate_from_pem(ca.certificate_pem)
        
        # Descifrar la clave privada de la CA
        decrypted_private_key_pem = crypto.decrypt(ca.private_key)
        ca_private_key = pki_utils.private_key_from_pem(decrypted_private_key_pem)
        
        # Generar la CRL firmada por esta CA
        crl_pem = pki_utils.generate_crl(ca_cert, ca_private_key, revoked_serials)
        
        return crl_pem
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating CRL: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
