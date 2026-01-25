"""
Modelos de base de datos
"""
from sqlalchemy import Column, String, LargeBinary, DateTime, Integer
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
