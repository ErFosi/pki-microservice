#!/usr/bin/env python3
"""
Script para generar una MASTER_KEY segura para el cifrado

Ejecuta este script y copia la clave generada al archivo .env
"""
from cryptography.fernet import Fernet


def generate_master_key():
    """Genera una clave maestra segura para Fernet"""
    key = Fernet.generate_key()
    return key.decode()


if __name__ == "__main__":
    print("=" * 60)
    print(" GENERADOR DE MASTER_KEY SEGURA")
    print("=" * 60)
    print()
    
    master_key = generate_master_key()
    
    print("Tu MASTER_KEY segura es:")
    print()
    print(f"    {master_key}")
    print()
    print("=" * 60)
    print(" INSTRUCCIONES IMPORTANTES:")
    print("=" * 60)
    print()
    print("1. Copia la clave de arriba")
    print("2. Pégala en tu archivo .env como:")
    print(f"   MASTER_KEY={master_key}")
    print()
    print("3. NUNCA compartas esta clave")
    print("4. NUNCA la commitees a Git")
    print("5. Si la pierdes, perderás acceso a las claves cifradas")
    print()
    print("=" * 60)
