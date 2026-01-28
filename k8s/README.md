# Kubernetes Deployment for PKI Microservice

This directory contains Kubernetes manifests for deploying the PKI microservice to a Kubernetes cluster.

## Architecture

The deployment consists of:

- **PostgreSQL Database**: Persistent storage for certificates and CAs
- **CA Service**: Core PKI operations (certificate signing, validation, revocation)
- **Auth Gateway**: Authentication and API gateway
- **Ingress**: External access routing

## Prerequisites

- Kubernetes cluster (v1.19+)
- kubectl configured to access the cluster
- NGINX Ingress Controller (for ingress)
- cert-manager (optional, for TLS certificates)
- Storage class for persistent volumes

## Quick Start

### 1. Update Secrets

Before deploying, update the sensitive values in `secret.yaml`:

```bash
# Generate secure keys
MASTER_KEY=$(python3 -c "from cryptography.fernet import Fernet; import base64; print(base64.b64encode(Fernet.generate_key()).decode())")
SECRET_KEY=$(python3 -c "import secrets; import base64; print(base64.b64encode(secrets.token_hex(32).encode()).decode())")

# Update the secret.yaml file with these values
```

### 2. Update Ingress

Edit `ingress.yaml` to use your domain:

```yaml
spec:
  tls:
  - hosts:
    - your-domain.com
  rules:
  - host: your-domain.com
```

### 3. Deploy

```bash
# Deploy all resources
kubectl apply -k k8s/

# Or deploy individually
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/ca-service.yaml
kubectl apply -f k8s/auth-gateway.yaml
kubectl apply -f k8s/ingress.yaml
```

### 4. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n pki-system

# Check services
kubectl get svc -n pki-system

# Check ingress
kubectl get ingress -n pki-system

# View logs
kubectl logs -n pki-system deployment/pki-ca-service
kubectl logs -n pki-system deployment/pki-auth-gateway
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@pki-postgres:5432/pki_db` |
| `MASTER_KEY` | Encryption key for private keys | **MUST BE SET** |
| `SECRET_KEY` | JWT signing key | **MUST BE SET** |
| `CA_SERVICE_URL` | Internal CA service URL | `http://pki-ca-service:8001` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiry | `30` |
| `DEBUG` | Debug mode | `False` |

### Resource Limits

Current resource requests/limits:
- **PostgreSQL**: 256Mi/512Mi RAM, 250m/500m CPU
- **CA Service**: 256Mi/512Mi RAM, 250m/500m CPU
- **Auth Gateway**: 128Mi/256Mi RAM, 100m/200m CPU

Adjust these in the deployment YAMLs based on your cluster capacity.

## Building Images

### Using Docker Build

```bash
# Build CA service image
docker build -t pki-ca-service:latest ./ca-service/

# Build auth gateway image
docker build -t pki-auth-gateway:latest ./auth-gateway/

# Push to registry
docker tag pki-ca-service:latest your-registry.com/pki-ca-service:latest
docker tag pki-auth-gateway:latest your-registry.com/pki-auth-gateway:latest
docker push your-registry.com/pki-ca-service:latest
docker push your-registry.com/pki-auth-gateway:latest
```

### Using CI/CD

Update the `kustomization.yaml` with your registry:

```yaml
images:
  - name: pki-ca-service
    newTag: v1.0.0
    newName: your-registry.com/pki-ca-service
  - name: pki-auth-gateway
    newTag: v1.0.0
    newName: your-registry.com/pki-auth-gateway
```

## Scaling

### Horizontal Scaling

```bash
# Scale CA service
kubectl scale deployment pki-ca-service -n pki-system --replicas=3

# Scale auth gateway
kubectl scale deployment pki-auth-gateway -n pki-system --replicas=2
```

### Database Scaling

For high availability, consider:
- PostgreSQL operator (e.g., Zalando PostgreSQL)
- Read replicas
- Connection pooling (PgBouncer)

## Monitoring

### Health Checks

All services include:
- Liveness probes: Restart container if unhealthy
- Readiness probes: Remove from service if not ready
- Health endpoints: `/health` for application health

### Logs

```bash
# View logs
kubectl logs -n pki-system -l app=pki-ca-service --tail=100 -f
kubectl logs -n pki-system -l app=pki-auth-gateway --tail=100 -f
```

### Metrics

Consider adding:
- Prometheus metrics
- Grafana dashboards
- AlertManager rules

## Backup and Recovery

### Database Backup

```bash
# Create backup
kubectl exec -n pki-system pki-postgres-0 -- pg_dump -U postgres pki_db > backup.sql

# Restore backup
kubectl exec -n pki-system pki-postgres-0 -- psql -U postgres pki_db < backup.sql
```

### Persistent Volumes

The PostgreSQL PVC ensures data persistence. For production:
- Use cloud-managed storage (EBS, Persistent Disk)
- Configure backup policies
- Test restore procedures

## Security Considerations

### Network Policies

Consider adding network policies to restrict traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: pki-network-policy
  namespace: pki-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
```

### Secrets Management

For production:
- Use external secret management (AWS Secrets Manager, Vault)
- Rotate keys regularly
- Audit secret access

### TLS

- Use cert-manager for automatic certificate renewal
- Configure HSTS headers
- Use strong cipher suites

## Troubleshooting

### Common Issues

1. **Pods not starting**: Check resource limits and node capacity
2. **Database connection errors**: Verify service names and ports
3. **Ingress not working**: Check ingress controller installation
4. **TLS certificate issues**: Verify cert-manager configuration

### Debug Commands

```bash
# Check pod status
kubectl describe pod -n pki-system <pod-name>

# Check service endpoints
kubectl get endpoints -n pki-system

# Test internal connectivity
kubectl exec -n pki-system -it pki-ca-service-0 -- curl http://pki-postgres:5432

# View events
kubectl get events -n pki-system --sort-by=.metadata.creationTimestamp
```

## Development

### Local Development

Use the docker-compose setup for local development:

```bash
docker-compose up -d
```

### Testing

```bash
# Port forward for local testing
kubectl port-forward -n pki-system svc/pki-auth-gateway 8000:8000

# Test endpoints
curl http://localhost:8000/health
```

## File Structure

```
k8s/
├── namespace.yaml          # Namespace definition
├── configmap.yaml          # Non-sensitive configuration
├── secret.yaml            # Sensitive configuration
├── postgres.yaml          # PostgreSQL deployment and service
├── ca-service.yaml        # CA service deployment and service
├── auth-gateway.yaml      # Auth gateway deployment and service
├── ingress.yaml           # Ingress configuration
└── kustomization.yaml     # Kustomize configuration
```