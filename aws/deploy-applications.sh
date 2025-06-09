#!/bin/bash

# Deploy StackAI Applications to EKS
# Run this script after the CDK infrastructure deployment completes

set -e

REGION="us-east-2"
CLUSTER_NAME="" # Will be populated from CDK outputs

echo "🚀 Deploying StackAI Applications to EKS..."

# 1. Configure kubectl
echo "📋 Configuring kubectl access..."
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME

# 2. Verify cluster access
echo "✅ Verifying cluster access..."
kubectl cluster-info
kubectl get nodes

# 3. Create application namespaces
echo "📁 Creating application namespaces..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: stackweb
---
apiVersion: v1
kind: Namespace
metadata:
  name: stackend
---
apiVersion: v1
kind: Namespace
metadata:
  name: stackrepl
---
apiVersion: v1
kind: Namespace
metadata:
  name: weaviate
---
apiVersion: v1
kind: Namespace
metadata:
  name: unstructured
EOF

# 4. Deploy Weaviate
echo "🔍 Deploying Weaviate..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weaviate
  namespace: weaviate
spec:
  replicas: 1
  selector:
    matchLabels:
      app: weaviate
  template:
    metadata:
      labels:
        app: weaviate
    spec:
      containers:
      - name: weaviate
        image: cr.weaviate.io/semitechnologies/weaviate:1.26.6
        ports:
        - containerPort: 8080
        env:
        - name: QUERY_DEFAULTS_LIMIT
          value: "25"
        - name: AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED
          value: "false"
        - name: AUTHENTICATION_APIKEY_ENABLED
          value: "true"
        - name: AUTHENTICATION_APIKEY_ALLOWED_KEYS
          value: "CHANGE_ME_WEAVIATE_API_KEY"
        - name: AUTHENTICATION_APIKEY_USERS
          value: "stackai"
        - name: PERSISTENCE_DATA_PATH
          value: "/var/lib/weaviate"
        - name: DEFAULT_VECTORIZER_MODULE
          value: "none"
        - name: ENABLE_MODULES
          value: ""
        - name: CLUSTER_HOSTNAME
          value: "node1"
        volumeMounts:
        - name: weaviate-data
          mountPath: /var/lib/weaviate
      volumes:
      - name: weaviate-data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: weaviate-svc
  namespace: weaviate
spec:
  selector:
    app: weaviate
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
EOF

# 5. Deploy Unstructured API
echo "📄 Deploying Unstructured API..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: unstructured
  namespace: unstructured
spec:
  replicas: 1
  selector:
    matchLabels:
      app: unstructured
  template:
    metadata:
      labels:
        app: unstructured
    spec:
      containers:
      - name: unstructured
        image: downloads.unstructured.io/unstructured-io/unstructured-api:0.0.80
        ports:
        - containerPort: 8000
        env:
        - name: UNSTRUCTURED_API_KEY
          value: "CHANGE_ME_UNSTRUCTURED_API_KEY"
---
apiVersion: v1
kind: Service
metadata:
  name: unstructured-svc
  namespace: unstructured
spec:
  selector:
    app: unstructured
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
EOF

# 6. Deploy StackEnd Backend + Celery
echo "⚙️ Deploying StackEnd Backend..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stackend-backend
  namespace: stackend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: stackend-backend
  template:
    metadata:
      labels:
        app: stackend-backend
    spec:
      containers:
      - name: stackend
        image: stackai/stackend:latest # You'll need to build and push this
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://postgres:PASSWORD@AURORA_ENDPOINT:5432/postgres"
        - name: REDIS_URL
          value: "redis://REDIS_ENDPOINT:6379/0"
        - name: WEAVIATE_URL
          value: "http://weaviate-svc.weaviate.svc.cluster.local:8080"
        - name: UNSTRUCTURED_URL
          value: "http://unstructured-svc.unstructured.svc.cluster.local:8000"
        # Add other environment variables as needed
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stackend-celery
  namespace: stackend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: stackend-celery
  template:
    metadata:
      labels:
        app: stackend-celery
    spec:
      containers:
      - name: celery-worker
        image: stackai/stackend:latest # Same image, different command
        command: ["celery", "worker", "-A", "stackend.celery", "--loglevel=info"]
        env:
        - name: DATABASE_URL
          value: "postgresql://postgres:PASSWORD@AURORA_ENDPOINT:5432/postgres"
        - name: REDIS_URL
          value: "redis://REDIS_ENDPOINT:6379/0"
---
apiVersion: v1
kind: Service
metadata:
  name: stackend-svc
  namespace: stackend
spec:
  selector:
    app: stackend-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
EOF

# 7. Deploy StackWeb Frontend
echo "🌐 Deploying StackWeb Frontend..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stackweb
  namespace: stackweb
spec:
  replicas: 2
  selector:
    matchLabels:
      app: stackweb
  template:
    metadata:
      labels:
        app: stackweb
    spec:
      containers:
      - name: stackweb
        image: stackai/stackweb:latest # You'll need to build and push this
        ports:
        - containerPort: 3000
        env:
        - name: NEXT_PUBLIC_SUPABASE_URL
          value: "https://api.stackai.com"
        - name: NEXT_PUBLIC_SUPABASE_ANON_KEY
          value: "YOUR_SUPABASE_ANON_KEY"
        - name: NEXT_PUBLIC_STACKEND_URL
          value: "https://backend.stackai.com"
---
apiVersion: v1
kind: Service
metadata:
  name: stackweb-svc
  namespace: stackweb
spec:
  selector:
    app: stackweb
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
EOF

# 8. Deploy StackRepl
echo "💻 Deploying StackRepl..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stackrepl
  namespace: stackrepl
spec:
  replicas: 1
  selector:
    matchLabels:
      app: stackrepl
  template:
    metadata:
      labels:
        app: stackrepl
    spec:
      containers:
      - name: stackrepl
        image: stackai/stackrepl:latest # You'll need to build and push this
        # Add environment variables as needed
EOF

# 9. Create Ingress for external access
echo "🌍 Creating Ingress for external access..."
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: stackai-main-ingress
  namespace: stackweb
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80},{"HTTPS":443}]'
spec:
  rules:
  - host: app.stackai.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: stackweb-svc
            port:
              number: 3000
  - host: api.stackai.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: gotrue-svc
            port:
              number: 9999
  - host: backend.stackai.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: stackend-svc
            port:
              number: 8000
EOF

echo "✅ Application deployment complete!"
echo ""
echo "⚠️  IMPORTANT: You still need to:"
echo "1. Build and push Docker images for StackWeb, StackEnd, StackRepl"
echo "2. Update connection strings with actual database/Redis endpoints"
echo "3. Configure proper API keys and secrets"
echo "4. Set up DNS records for your domains"
echo "5. Configure SSL certificates"
echo ""
echo "📋 Check deployment status:"
echo "kubectl get pods -A"
echo "kubectl get ingress -A" 