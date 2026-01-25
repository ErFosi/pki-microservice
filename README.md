# PKI Microservice

Sistema de infraestructura de clave pública (PKI) con microservicios.

## Arquitectura

- **ca-service**: Servicio de Autoridad Certificadora (CA) con cifrado de claves privadas
- **auth-gateway**: Gateway de autenticación (próximamente)
- **PostgreSQL**: Base de datos para persistencia

##  Seguridad

Las claves privadas de las CAs se almacenan **CIFRADAS** en la base de datos usando una `MASTER_KEY`. 

### Generar MASTER_KEY

**Opción 1 - Usando el script incluido (Recomendado):**
```bash
python3 ca-service/generate_master_key.py
```

**Opción 2 - Comando directo:**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Opción 3 - OpenSSL:**
```bash
openssl rand -base64 32
```

Luego copia la clave generada a tu archivo `.env`:
```
MASTER_KEY=tu_clave_generada_aqui
```

 **IMPORTANTE, TEMA CIFRADO**: 
- NUNCA commitees el archivo `.env` a Git
- Si pierdes la `MASTER_KEY`, perderás acceso a las claves privadas cifradas
- Usa una clave diferente para desarrollo y producción

##  Inicio

### 1. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp example.env .env

# Generar una MASTER_KEY segura
python3 ca-service/generate_master_key.py

# Editar .env y pegar la MASTER_KEY generada
nano .env
```

### 2. Levantar los servicios

```bash
docker-compose up --build
```

### 3. Probar el cifrado

Accede a la documentación interactiva:
```
http://localhost:8001/docs
```

Prueba el endpoint `/test/encryption`:
```bash
curl -X POST "http://localhost:8001/test/encryption" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hola Mundo Secreto"}'
```

Se deberia recibir una respuesta similar a:
```json
{
  "original": "Hola Mundo Secreto",
  "encrypted_hex": "6741414141424...",
  "decrypted": "Hola Mundo Secreto",
  "match": true
}
```

## 📋 Endpoints

### CA Service (Puerto 8001)

- `GET /health` - Health check
- `POST /test/encryption` - Probar cifrado/descifrado (solo testing)
- `GET /docs` - Documentación Swagger

## Modelo de Base de Datos

### Tabla: certificate_authorities 

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | Primary key |
| common_name | String(255) | Nombre común de la CA (único) |
| private_key | LargeBinary | Clave privada **CIFRADA** |
| certificate_pem | String | Certificado en formato PEM |
| created_at | DateTime | Fecha de creación |

### FALTAN TABLAS, OTRAS FEATURES...

## Estructura del Proyecto

```
pki-microservice/
├── ca-service/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuración
│   ├── database.py          # Setup de SQLAlchemy
│   ├── models.py            # Modelos de DB
│   ├── schemas.py           # Esquemas Pydantic
│   ├── crypto_utils.py      # Utilidades de cifrado
│   ├── generate_master_key.py  # Script para generar MASTER_KEY
│   ├── requirements.txt     # Dependencias
│   └── Dockerfile
├── auth-gateway/
│   ├── main.py
│   └── Dockerfile
├── docker-compose.yml
├── example.env              # Ejemplo de variables de entorno
├── .env                     # Variables de entorno (NO commitear)
└── README.md
```

## 🔍 Verificar la Configuración

```bash
# Ver logs del servicio
docker-compose logs -f ca-service

# Entrar al contenedor de la DB
docker-compose exec db psql -U postgres -d pki_db

# Verificar tablas creadas
\dt

# Ver estructura de la tabla
\d certificate_authorities
```

## 🧪 Testing del Cifrado

El endpoint `/test/encryption` te permite verificar que:
1. La `MASTER_KEY` está configurada correctamente
2. El cifrado funciona
3. El descifrado recupera el texto original
4. Los datos coinciden

## 📝 Próximos Pasos

- [ ] Implementar creación de CAs
- [ ] Generar certificados firmados
- [ ] Implementar autenticación en auth-gateway
- [ ] Agregar endpoints de gestión de certificados
