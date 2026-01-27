"""
Utilidades PKI para gestión de Certificate Authorities y certificados

Funciones para:
- Generar CAs autofirmadas
- Firmar Certificate Signing Requests (CSR)
- Validar certificados
- Gestionar Certificate Revocation Lists (CRL)
"""
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import secrets


def generate_private_key(key_size: int = 2048) -> rsa.RSAPrivateKey:
    """
    Genera una clave privada RSA
    
    Args:
        key_size: Tamaño de la clave en bits (2048 o 4096)
    
    Returns:
        Clave privada RSA
    """
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )


def private_key_to_pem(private_key: rsa.RSAPrivateKey) -> bytes:
    """
    Serializa una clave privada a formato PEM
    
    Args:
        private_key: Clave privada RSA
    
    Returns:
        Clave en formato PEM (bytes)
    """
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )


def private_key_from_pem(pem_data: bytes) -> rsa.RSAPrivateKey:
    """
    Deserializa una clave privada desde formato PEM
    
    Args:
        pem_data: Clave en formato PEM (bytes)
    
    Returns:
        Clave privada RSA
    """
    return serialization.load_pem_private_key(pem_data, password=None)


def generate_ca_certificate(
    common_name: str,
    private_key: rsa.RSAPrivateKey,
    validity_days: int = 3650
) -> x509.Certificate:
    """
    Genera un certificado autofirmado para una CA
    
    Args:
        common_name: Nombre común de la CA
        private_key: Clave privada de la CA
        validity_days: Días de validez del certificado (default: 10 años)
    
    Returns:
        Certificado X.509 autofirmado
    """
    # Subject y Issuer son iguales (autofirmado)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Gipuzkoa"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Arrasate"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Ikerlan"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    # Generar número de serie único
    serial_number = x509.random_serial_number()
    
    # Fechas de validez
    not_valid_before = datetime.utcnow()
    not_valid_after = not_valid_before + timedelta(days=validity_days)
    
    # Construir el certificado
    cert_builder = x509.CertificateBuilder()
    cert_builder = cert_builder.subject_name(subject)
    cert_builder = cert_builder.issuer_name(issuer)
    cert_builder = cert_builder.public_key(private_key.public_key())
    cert_builder = cert_builder.serial_number(serial_number)
    cert_builder = cert_builder.not_valid_before(not_valid_before)
    cert_builder = cert_builder.not_valid_after(not_valid_after)
    
    # Extensiones de CA
    cert_builder = cert_builder.add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    )
    cert_builder = cert_builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_cert_sign=True,
            crl_sign=True,
            key_encipherment=False,
            content_commitment=False,
            data_encipherment=False,
            key_agreement=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )
    cert_builder = cert_builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
        critical=False,
    )
    
    # Firmar el certificado con la clave privada de la CA
    certificate = cert_builder.sign(private_key, hashes.SHA256())
    
    return certificate


def certificate_to_pem(certificate: x509.Certificate) -> str:
    """
    Serializa un certificado a formato PEM
    
    Args:
        certificate: Certificado X.509
    
    Returns:
        Certificado en formato PEM (string)
    """
    return certificate.public_bytes(serialization.Encoding.PEM).decode('utf-8')


def certificate_from_pem(pem_data: str) -> x509.Certificate:
    """
    Deserializa un certificado desde formato PEM
    
    Args:
        pem_data: Certificado en formato PEM (string)
    
    Returns:
        Certificado X.509
    """
    return x509.load_pem_x509_certificate(pem_data.encode('utf-8'))


def csr_from_pem(pem_data: str) -> x509.CertificateSigningRequest:
    """
    Deserializa un CSR desde formato PEM
    
    Args:
        pem_data: CSR en formato PEM (string)
    
    Returns:
        Certificate Signing Request
    """
    return x509.load_pem_x509_csr(pem_data.encode('utf-8'))


def sign_csr(
    csr: x509.CertificateSigningRequest,
    ca_certificate: x509.Certificate,
    ca_private_key: rsa.RSAPrivateKey,
    validity_days: int = 365
) -> x509.Certificate:
    """
    Firma un CSR con una CA y genera un certificado
    
    Args:
        csr: Certificate Signing Request
        ca_certificate: Certificado de la CA
        ca_private_key: Clave privada de la CA
        validity_days: Días de validez del certificado (default: 1 año)
    
    Returns:
        Certificado X.509 firmado por la CA
    """
    # Verificar la firma del CSR
    if not csr.is_signature_valid:
        raise ValueError("CSR signature is invalid")
    
    # Generar número de serie único
    serial_number = x509.random_serial_number()
    
    # Fechas de validez
    not_valid_before = datetime.utcnow()
    not_valid_after = not_valid_before + timedelta(days=validity_days)
    
    # Construir el certificado
    cert_builder = x509.CertificateBuilder()
    cert_builder = cert_builder.subject_name(csr.subject)
    cert_builder = cert_builder.issuer_name(ca_certificate.subject)
    cert_builder = cert_builder.public_key(csr.public_key())
    cert_builder = cert_builder.serial_number(serial_number)
    cert_builder = cert_builder.not_valid_before(not_valid_before)
    cert_builder = cert_builder.not_valid_after(not_valid_after)
    
    # Extensiones básicas
    cert_builder = cert_builder.add_extension(
        x509.BasicConstraints(ca=False, path_length=None),
        critical=True,
    )
    cert_builder = cert_builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            content_commitment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    )
    cert_builder = cert_builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(csr.public_key()),
        critical=False,
    )
    cert_builder = cert_builder.add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_private_key.public_key()),
        critical=False,
    )
    
    # Firmar el certificado con la CA
    certificate = cert_builder.sign(ca_private_key, hashes.SHA256())
    
    return certificate


def validate_certificate(
    certificate: x509.Certificate,
    ca_certificate: x509.Certificate
) -> bool:
    """
    Valida que un certificado esté firmado por una CA específica
    
    Args:
        certificate: Certificado a validar
        ca_certificate: Certificado de la CA
    
    Returns:
        True si el certificado es válido, False en caso contrario
    """
    try:
        # Verificar que el issuer del certificado coincida con el subject de la CA
        if certificate.issuer != ca_certificate.subject:
            return False
        
        # Verificar la firma del certificado usando la clave pública de la CA
        ca_public_key = ca_certificate.public_key()
        
        # Para RSA, verificar usando el algoritmo de firma del certificado
        from cryptography.hazmat.primitives.asymmetric import padding
        
        ca_public_key.verify(
            certificate.signature,
            certificate.tbs_certificate_bytes,
            padding.PKCS1v15(),
            certificate.signature_hash_algorithm
        )
        
        # Verificar fechas de validez
        now = datetime.now().replace(tzinfo=None)
        not_before = certificate.not_valid_before_utc.replace(tzinfo=None)
        not_after = certificate.not_valid_after_utc.replace(tzinfo=None)
        
        if now < not_before or now > not_after:
            return False
        
        return True
    except Exception as e:
        # Para debugging
        print(f"Validation error: {e}")
        return False


def get_certificate_serial_number(certificate: x509.Certificate) -> str:
    """
    Obtiene el número de serie de un certificado
    
    Args:
        certificate: Certificado X.509
    
    Returns:
        Número de serie en formato hexadecimal
    """
    return format(certificate.serial_number, 'x')


def get_certificate_common_name(certificate: x509.Certificate) -> str:
    """
    Obtiene el Common Name de un certificado
    
    Args:
        certificate: Certificado X.509
    
    Returns:
        Common Name del certificado
    """
    return certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
