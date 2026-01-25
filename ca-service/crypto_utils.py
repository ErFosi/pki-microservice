"""
Utilidades de cifrado/descifrado para datos sensibles

Usa Fernet (AES-128 en modo CBC con HMAC para autenticación)
NUNCA almacenes claves privadas en texto plano.
"""
from cryptography.fernet import Fernet
from config import get_settings
import base64
import hashlib


class CryptoHelper:
    """
    Helper para cifrar/descifrar datos sensibles usando la MASTER_KEY
    """
    
    def __init__(self):
        settings = get_settings()
        # Fernet requiere una clave de exactamente 32 bytes (base64 encoded)
        # Derivamos la clave desde la MASTER_KEY usando SHA-256
        self._fernet = self._get_fernet_from_master_key(settings.MASTER_KEY)
    
    @staticmethod
    def _get_fernet_from_master_key(master_key: str) -> Fernet:
        """
        Convierte la MASTER_KEY en una clave válida para Fernet
        
        Args:
            master_key: La clave maestra desde el .env
            
        Returns:
            Instancia de Fernet lista para usar
        """
        # Usar SHA-256 para derivar una clave de 32 bytes
        key_bytes = hashlib.sha256(master_key.encode()).digest()
        # Fernet necesita la clave en base64
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        return Fernet(fernet_key)
    
    def encrypt(self, data: bytes) -> bytes:
        """
        Cifra datos binarios
        
        Args:
            data: Datos en bytes para cifrar
            
        Returns:
            Datos cifrados en bytes
        """
        return self._fernet.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        Descifra datos binarios
        
        Args:
            encrypted_data: Datos cifrados en bytes
            
        Returns:
            Datos originales en bytes
            
        Raises:
            cryptography.fernet.InvalidToken: Si la clave es incorrecta o los datos están corruptos
        """
        return self._fernet.decrypt(encrypted_data)
    
    def encrypt_string(self, text: str) -> bytes:
        """
        Cifra un string
        
        Args:
            text: String para cifrar
            
        Returns:
            Datos cifrados en bytes
        """
        return self.encrypt(text.encode('utf-8'))
    
    def decrypt_string(self, encrypted_data: bytes) -> str:
        """
        Descifra a un string
        
        Args:
            encrypted_data: Datos cifrados en bytes
            
        Returns:
            String original
        """
        return self.decrypt(encrypted_data).decode('utf-8')


# Singleton global
_crypto_helper = None


def get_crypto_helper() -> CryptoHelper:
    """
    Obtiene la instancia singleton del CryptoHelper
    """
    global _crypto_helper
    if _crypto_helper is None:
        _crypto_helper = CryptoHelper()
    return _crypto_helper
