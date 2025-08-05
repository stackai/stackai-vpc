# Redis on Azure Kubernetes Service (AKS)

This configuration deploys Redis using the Bitnami Helm chart with AKS-specific optimizations.

## Architecture
- Master-Replica configuration with 1 master and 2 replicas
- Persistent storage using Azure Premium SSD
- Internal load balancer for master service
- Metrics enabled for monitoring

## Storage
Uses Azure Managed Disks with Premium SSD performance tier:
- Master: 32Gi
- Replicas: 32Gi each
- StorageClass: `redis-premium-rwo`

## Installation
```bash
# Create namespace
kubectl create namespace redis

# Apply the configuration
kubectl apply -k .
```

## Access Redis
```bash
# Get the Redis password
export REDIS_PASSWORD=$(kubectl get secret --namespace redis redis -o jsonpath="{.data.redis-password}" | base64 -d)

# Connect to Redis master
kubectl run --namespace redis redis-client --restart='Never' --env REDIS_PASSWORD=$REDIS_PASSWORD --image docker.io/bitnami/redis:7.4 --command -- sleep infinity
kubectl exec --tty -i redis-client --namespace redis -- bash

# Inside the pod
redis-cli -h redis-master -a $REDIS_PASSWORD
```