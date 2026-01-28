#!/bin/bash

# PKI Microservice Kubernetes Deployment Script

set -e

NAMESPACE="pki-system"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Deploying PKI Microservice to Kubernetes"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if we're connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Not connected to a Kubernetes cluster."
    exit 1
fi

echo "📦 Creating namespace..."
kubectl apply -f "$SCRIPT_DIR/namespace.yaml"

echo "🔧 Applying configuration..."
kubectl apply -f "$SCRIPT_DIR/configmap.yaml"
kubectl apply -f "$SCRIPT_DIR/secret.yaml"

echo "🗄️ Deploying PostgreSQL..."
kubectl apply -f "$SCRIPT_DIR/postgres.yaml"

echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/pki-postgres -n $NAMESPACE

echo "🔐 Deploying CA Service..."
kubectl apply -f "$SCRIPT_DIR/ca-service.yaml"

echo "⏳ Waiting for CA Service to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/pki-ca-service -n $NAMESPACE

echo "🌐 Deploying Auth Gateway..."
kubectl apply -f "$SCRIPT_DIR/auth-gateway.yaml"

echo "⏳ Waiting for Auth Gateway to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/pki-auth-gateway -n $NAMESPACE

echo "🌐 Deploying Ingress..."
kubectl apply -f "$SCRIPT_DIR/ingress.yaml"

echo "✅ Deployment completed!"
echo ""
echo "📊 Checking status..."
kubectl get pods -n $NAMESPACE
kubectl get svc -n $NAMESPACE
kubectl get ingress -n $NAMESPACE

echo ""
echo "🔗 Service URLs:"
echo "Internal CA Service: http://pki-ca-service.pki-system.svc.cluster.local:8001"
echo "Auth Gateway: Check ingress for external URL"

echo ""
echo "📖 See k8s/README.md for detailed documentation"
echo "🩺 Run 'kubectl logs -n pki-system deployment/pki-ca-service' to check logs"