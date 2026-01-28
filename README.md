# PKI Microservice

Sistema de infraestructura de clave pública (PKI) con microservicios.

## Arquitectura

- **auth-gateway** (Puerto 8000): Gateway de autenticación JWT y proxy reverso
- **ca-service** (Puerto 8001): Servicio de Autoridad Certificadora (CA) con cifrado de claves privadas
- **PostgreSQL** (Puerto 5432): Base de datos para persistencia

### Flujo de Autenticación

```
Cliente -> Auth Gateway -> CA Service
   1. POST /login (obtener token JWT)
   2. GET /crypto/* con Bearer token
   3. Gateway valida token
   4. Gateway proxy a CA Service
   5. Respuesta al cliente
```

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
- NUNCA se commitea el archivo `.env` a Git, hay un example.env pero de plantilla nada mas.
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

### 3. Obtener token de autenticación

Primero, obtén un token JWT:
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"ikerlan","password":"ikerlan"}'
```

Respuesta:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 4. Probar el cifrado (a través del proxy)

Usa el token para acceder al ca-service a través del gateway:
```bash
TOKEN="tu_token_aqui"

curl -X POST "http://localhost:8000/crypto/test/encryption" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hola Mundo Secreto"}'
```

### 5. Acceso directo al CA Service (sin autenticación - solo desarrollo)

```bash
curl -X POST "http://localhost:8001/test/encryption" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hola Mundo Secreto"}'
```

Respuesta esperada:
```json
{
  "original": "Hola Mundo Secreto",
  "encrypted_hex": "6741414141424...",
  "decrypted": "Hola Mundo Secreto",
  "match": true
}
```

## Endpoints

### Auth Gateway (Puerto 8000) - Punto de entrada principal

- `POST /login` - Autenticación (retorna JWT token)
  - Credenciales: `username: ikerlan`, `password: ikerlan`
- `GET|POST|PUT|DELETE|PATCH /crypto/*` - Proxy a CA Service (requiere autenticación)
- `GET /health` - Health check
- `GET /docs` - Documentación Swagger

**Ejemplo de uso:**
```bash
# 1. Login
TOKEN=$(curl -s -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"ikerlan","password":"ikerlan"}' | jq -r '.access_token')

# 2. Usar el token
curl -X POST "http://localhost:8000/crypto/test/encryption" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Prueba"}'
```

### CA Service (Puerto 8001) - Acceso directo (solo desarrollo)

#### Endpoints de Testing
- `GET /health` - Health check
- `POST /test/encryption` - Probar cifrado/descifrado (solo testing)
- `GET /docs` - Documentación Swagger

#### Endpoints de CA (Certificate Authority)

**Crear una CA:**
- `POST /ca` - Crear una nueva Certificate Authority
  ```bash
  curl -X POST "http://localhost:8001/ca" \
    -H "Content-Type: application/json" \
    -d '{"common_name": "MiCA"}'
  ```

**Firmar un CSR:**
- `POST /crt` - Firmar un Certificate Signing Request
  - `csr` (requerido): CSR en formato PEM
  - `ca_common_name` (opcional): Nombre de la CA a utilizar. Si no se especifica, usa la primera disponible
  ```bash
  curl -X POST "http://localhost:8001/crt" \
    -H "Content-Type: application/json" \
    -d '{
      "csr": "-----BEGIN CERTIFICATE REQUEST-----\n...\n-----END CERTIFICATE REQUEST-----",
      "ca_common_name": "MiCA"
    }'
  ```

**Validar un Certificado:**
- `POST /validate` - Validar un certificado
  - `crt` (requerido): Certificado en formato PEM
  - `ca_common_name` (opcional): CA emisora. Si no se especifica, se extrae automáticamente del certificado
  ```bash
  curl -X POST "http://localhost:8001/validate" \
    -H "Content-Type: application/json" \
    -d '{
      "crt": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"
    }'
  ```

**Revocar un Certificado:**
- `POST /cert/revoke/{cert_id}` - Revocar un certificado
  ```bash
  curl -X POST "http://localhost:8001/cert/revoke/1" \
    -H "Content-Type: application/json" \
    -d '{"reason": "Compromiso de clave privada"}'
  ```

**Obtener CRL:**
- `GET /crl` - Obtener la Certificate Revocation List en formato PEM
  ```bash
  curl "http://localhost:8001/crl"
  ```

 **En producción, el CA Service debe estar solo accesible internamente (via auth-gateway)**

## Modelo de Base de Datos

### Tabla: certificate_authorities 

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | Primary key |
| common_name | String(255) | Nombre común de la CA (único) |
| private_key | LargeBinary | Clave privada **CIFRADA** |
| certificate_pem | String | Certificado en formato PEM |
| created_at | DateTime | Fecha de creación |

### Tabla: certificates

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | Primary key |
| serial_number | String(64) | Número de serie del certificado (único) |
| common_name | String(255) | Nombre común del certificado |
| certificate_pem | String | Certificado en formato PEM |
| ca_id | Integer | Foreign key a certificate_authorities |
| created_at | DateTime | Fecha de creación |
| expires_at | DateTime | Fecha de expiración |

### Tabla: revoked_certificates

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | Primary key |
| certificate_id | Integer | Foreign key a certificates (único) |
| serial_number | String(64) | Número de serie del certificado revocado |
| revoked_at | DateTime | Fecha de revocación |
| reason | String(255) | Razón de la revocación |

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

## Verificar la Configuración

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

## Testing del Cifrado

El endpoint `/test/encryption` te permite verificar que:
1. La `MASTER_KEY` está configurada correctamente
2. El cifrado funciona
3. El descifrado recupera el texto original
4. Los datos coinciden

## Despliegue en Kubernetes

El proyecto incluye manifiestos de Kubernetes para desplegar en un cluster.

### Prerequisitos

- Cluster de Kubernetes (minikube, GKE, EKS, AKS, etc.)
- kubectl configurado
- Imágenes Docker construidas y disponibles en un registry

### Estructura de Archivos K8s

```
k8s/
├── namespace.yaml                    # Namespace pki-system
├── configmap.yaml                    # Configuración no sensible
├── secret.yaml                       # Claves y secrets (MASTER_KEY, SECRET_KEY)
├── postgres-deployment.yaml          # Deployment y PVC de PostgreSQL
├── postgres-service.yaml             # Service para PostgreSQL
├── ca-service-deployment.yaml        # Deployment del CA Service
├── ca-service-service.yaml           # Service del CA Service
├── auth-gateway-deployment.yaml      # Deployment del Auth Gateway
├── auth-gateway-service.yaml         # Service del Auth Gateway (LoadBalancer)
├── ingress.yaml                      # Ingress para acceso externo
├── kustomization.yaml                # Kustomize para gestionar recursos
└── deploy.sh                         # Script de despliegue automatizado
```

### Despliegue Rápido

#### 1. Actualizar Secrets

Antes de desplegar, genera claves seguras:

```bash
# Generar MASTER_KEY
MASTER_KEY=$(python3 -c "from cryptography.fernet import Fernet; import base64; print(base64.b64encode(Fernet.generate_key()).decode())")

# Generar SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; import base64; print(base64.b64encode(secrets.token_hex(32).encode()).decode())")

# Editar k8s/secret.yaml con los valores generados
```

#### 2. Construir y Cargar Imágenes

Para minikube:
```bash
# Construir imágenes
docker build -t pki-ca-service:latest ./ca-service/
docker build -t pki-auth-gateway:latest ./auth-gateway/

# Cargar en minikube
minikube image load pki-ca-service:latest
minikube image load pki-auth-gateway:latest
```

Para clusters en la nube, pushea las imágenes a tu registry:
```bash
# Tag y push
docker tag pki-ca-service:latest tu-registry.com/pki-ca-service:latest
docker tag pki-auth-gateway:latest tu-registry.com/pki-auth-gateway:latest
docker push tu-registry.com/pki-ca-service:latest
docker push tu-registry.com/pki-auth-gateway:latest

# Actualizar kustomization.yaml con tu registry
```

#### 3. Desplegar

Opción 1 - Usando el script:
```bash
cd k8s
./deploy.sh
```

Opción 2 - Manual:
```bash
cd k8s
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f postgres-service.yaml
kubectl apply -f ca-service-deployment.yaml
kubectl apply -f ca-service-service.yaml
kubectl apply -f auth-gateway-deployment.yaml
kubectl apply -f auth-gateway-service.yaml
kubectl apply -f ingress.yaml
```

Opción 3 - Con Kustomize:
```bash
kubectl apply -k k8s/
```

### Verificar el Despliegue

```bash
# Ver todos los recursos en el namespace
kubectl get all -n pki-system

# Ver logs del CA Service
kubectl logs -n pki-system deployment/pki-ca-service -f

# Ver logs del Auth Gateway
kubectl logs -n pki-system deployment/pki-auth-gateway -f

# Verificar estado de los pods
kubectl get pods -n pki-system

# Describir un pod específico
kubectl describe pod -n pki-system <pod-name>
```

### Acceder a los Servicios

Para minikube:
```bash
# Obtener URL del servicio
minikube service pki-auth-gateway -n pki-system --url

# O hacer port-forward
kubectl port-forward -n pki-system svc/pki-auth-gateway 8000:8000
```

Para clusters con LoadBalancer:
```bash
# Obtener IP externa
kubectl get svc -n pki-system pki-auth-gateway
```

Con Ingress configurado:
```bash
# Acceder vía el dominio configurado en ingress.yaml
curl https://pki.tu-dominio.com/health
```

### Escalar los Servicios

```bash
# Escalar CA Service
kubectl scale deployment pki-ca-service -n pki-system --replicas=3

# Escalar Auth Gateway
kubectl scale deployment pki-auth-gateway -n pki-system --replicas=2
```

### Actualizar la Aplicación

```bash
# Reconstruir imagen
docker build -t pki-ca-service:v2 ./ca-service/

# Cargar en minikube o push a registry
minikube image load pki-ca-service:v2

# Actualizar el deployment
kubectl set image deployment/pki-ca-service pki-ca-service=pki-ca-service:v2 -n pki-system

# O editar el deployment
kubectl edit deployment pki-ca-service -n pki-system
```

### Eliminar el Despliegue

```bash
# Eliminar todo el namespace (cuidado!)
kubectl delete namespace pki-system

# O eliminar recursos individuales
kubectl delete -f k8s/
```

### Consideraciones de Producción

1. **Secrets**: Usar sistemas externos como AWS Secrets Manager, HashiCorp Vault, o Sealed Secrets
2. **Persistencia**: Configurar StorageClass apropiado para PostgreSQL
3. **Backups**: Implementar backups automáticos de la base de datos
4. **Monitoring**: Agregar Prometheus y Grafana para métricas
5. **Logs**: Centralizar logs con ELK Stack o similar
6. **TLS**: Configurar cert-manager para certificados TLS automáticos
7. **Network Policies**: Restringir tráfico entre pods
8. **Resource Limits**: Ajustar requests y limits según carga real
9. **High Availability**: Configurar PostgreSQL con replicación
10. **Ingress Controller**: Instalar NGINX Ingress Controller o similar

Para más detalles, consultar [k8s/README.md](k8s/README.md).

