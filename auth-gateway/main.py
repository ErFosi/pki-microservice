"""
Auth Gateway - Gateway de autenticación y proxy

Este servicio actúa como:
1. Servidor de autenticación (genera tokens JWT)
2. Proxy reverso hacia ca-service (valida tokens)

Endpoints:
- POST /login - Autenticación y generación de token
- ANY /crypto/* - Proxy hacia ca-service (requiere autenticación)
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import Response
from datetime import timedelta
import httpx

from config import get_settings
from schemas import LoginRequest, Token, TokenData
from auth import create_access_token, authenticate_user, verify_token

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Gateway de autenticación y proxy para servicios PKI",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "endpoints": {
            "login": "POST /login",
            "crypto_service": "/crypto/* (requiere autenticación)",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }


@app.post("/login", response_model=Token)
async def login(credentials: LoginRequest):
    """
    Endpoint de autenticación
    
    Credenciales válidas (hardcoded):
    - Username: ikerlan
    - Password: ikerlan
    
    Returns:
        Token JWT con tiempo de expiración
    """
    # Autenticar usuario
    if not authenticate_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": credentials.username},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@app.api_route("/crypto/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_ca_service(
    request: Request,
    path: str,
    token_data: TokenData = Depends(verify_token)
):
    """
    Proxy reverso hacia ca-service
    
    Este endpoint:
    1. Valida el token JWT (usando verify_token)
    2. Reenvía la petición al ca-service
    3. Devuelve la respuesta del ca-service
    
    Todas las rutas /crypto/* requieren autenticación
    """
    # Construir la URL del servicio de destino
    target_url = f"{settings.CA_SERVICE_URL}/{path}"
    
    # Copiar query parameters
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"
    
    # Preparar headers (eliminar host y otros headers problemáticos)
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("authorization", None)  # No reenviar el token
    
    # Leer el body si existe
    body = await request.body()
    
    # Hacer la petición al ca-service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                timeout=30.0
            )
            
            # Devolver la respuesta del ca-service
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
            
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error al comunicarse con ca-service: {str(e)}"
            )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
