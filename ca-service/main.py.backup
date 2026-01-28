"""
CA Service - Servicio de Autoridad Certificadora

Endpoints:
- POST /test/encryption - Prueba de cifrado/descifrado
- POST /ca - Crear una CA (próximamente)
- GET /health - Health check
"""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from database import get_db, init_db
from crypto_utils import get_crypto_helper, CryptoHelper
from schemas import EncryptionTestRequest, EncryptionTestResponse
from config import get_settings

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
    version="0.1.0",
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
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
