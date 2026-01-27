"""
Utilidades de autenticación JWT
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import get_settings
from schemas import TokenData

settings = get_settings()

# Security scheme para Bearer token
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT
    
    Args:
        data: Datos a incluir en el token (payload)
        expires_delta: Tiempo de expiración opcional
        
    Returns:
        Token JWT como string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Verifica y decodifica un token JWT
    
    Dependencia de FastAPI para proteger endpoints
    
    Args:
        credentials: Credenciales del header Authorization
        
    Returns:
        Datos del token decodificado
        
    Raises:
        HTTPException: Si el token es inválido
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extraer el token
        token = credentials.credentials
        
        # Decodificar el JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(username=username)
        
    except JWTError:
        raise credentials_exception
    
    return token_data


def authenticate_user(username: str, password: str) -> bool:
    """
    Autentica un usuario
    
    ⚠️ HARDCODED para la demo - En producción usar una base de datos
    
    Args:
        username: Nombre de usuario
        password: Contraseña
        
    Returns:
        True si las credenciales son válidas
    """
    # Credenciales hardcodeadas
    VALID_USERNAME = "ikerlan"
    VALID_PASSWORD = "ikerlan"
    
    return username == VALID_USERNAME and password == VALID_PASSWORD
