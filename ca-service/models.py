"""
Modelos de base de datos
"""
from sqlalchemy import Column, String, LargeBinary, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.sql import func
from database import Base


class CertificateAuthority(Base):
    """
    Modelo para almacenar las Certificate Authorities (CAs)
    
    La private_key se almacena CIFRADA usando la MASTER_KEY
    """
    __tablename__ = "certificate_authorities"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    common_name = Column(String(255), unique=True, nullable=False, index=True)
    private_key = Column(LargeBinary, nullable=False)  # Cifrada con MASTER_KEY
    certificate_pem = Column(String, nullable=False)   # Certificado en formato PEM
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<CertificateAuthority(id={self.id}, common_name={self.common_name})>"


class Certificate(Base):
    """
    Modelo para almacenar certificados emitidos por las CAs
    """
    __tablename__ = "certificates"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    serial_number = Column(String(64), unique=True, nullable=False, index=True)
    common_name = Column(String(255), nullable=False, index=True)
    certificate_pem = Column(String, nullable=False)
    ca_id = Column(Integer, ForeignKey("certificate_authorities.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    def __repr__(self):
        return f"<Certificate(id={self.id}, serial={self.serial_number}, cn={self.common_name})>"


class RevokedCertificate(Base):
    """
    Modelo para la Certificate Revocation List (CRL)
    """
    __tablename__ = "revoked_certificates"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    certificate_id = Column(Integer, ForeignKey("certificates.id"), unique=True, nullable=False)
    serial_number = Column(String(64), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reason = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<RevokedCertificate(cert_id={self.certificate_id}, serial={self.serial_number})>"
