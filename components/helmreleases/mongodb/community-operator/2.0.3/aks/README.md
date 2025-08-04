# MongoDB Community Operator on AKS

This overlay configures the MongoDB Community Operator for deployment on Azure Kubernetes Service (AKS).

## Azure-Specific Configurations

### Storage Configuration
- Uses Azure Disk CSI driver with Premium SSD storage (`Premium_LRS`)
- **IMPORTANT**: We use `disk.csi.azure.com` instead of `file.csi.azure.com` because MongoDB requires block storage for optimal performance and data consistency
- Storage class configured with:
  - `ReadOnly` caching mode for better read performance
  - `Retain` reclaim policy to prevent accidental data loss
  - Volume expansion enabled for growing databases

### Resource Optimizations
- Operator resources increased to handle Azure's workload patterns:
  - CPU: 1000m request / 2000m limit
  - Memory: 500Mi request / 2Gi limit
- MongoDB instance resources configured for production use:
  - MongoDB container: 1000m CPU / 2Gi memory (requests), 2000m CPU / 4Gi memory (limits)
  - MongoDB Agent: 250m CPU / 250Mi memory (requests), 500m CPU / 500Mi memory (limits)

### Networking
- Internal load balancer configured for security (`service.beta.kubernetes.io/azure-load-balancer-internal: "true"`)
- Ensures MongoDB instances are not exposed to the internet

## Deployment

Deploy using Flux CD:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: mongodb-community-operator
  namespace: flux-system
spec:
  interval: 10m
  path: "./components/helmreleases/mongodb/community-operator/2.0.3/aks"
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
```

## Creating MongoDB Instances

After the operator is deployed, you can create MongoDB instances using the `MongoDBCommunity` CRD. Example:

```yaml
apiVersion: mongodbcommunity.mongodb.com/v1
kind: MongoDBCommunity
metadata:
  name: mongodb-replica-set
  namespace: mongodb
spec:
  members: 3
  type: ReplicaSet
  version: "6.0.3"
  security:
    authentication:
      modes: ["SCRAM"]
  users:
    - name: admin
      db: admin
      passwordSecretRef:
        name: admin-password
      roles:
        - name: clusterAdmin
          db: admin
        - name: userAdminAnyDatabase
          db: admin
      scramCredentialsSecretName: admin-scram
  statefulSet:
    spec:
      volumeClaimTemplates:
        - metadata:
            name: data-volume
          spec:
            storageClassName: mongodb-premium-ssd
            accessModes: ["ReadWriteOnce"]
            resources:
              requests:
                storage: 100Gi
```

## Important Notes

1. **Storage Performance**: Premium SSD is recommended for production workloads to ensure consistent I/O performance
2. **Backup Strategy**: Implement regular backups using Azure Backup or MongoDB's native backup tools
3. **Monitoring**: Consider integrating with Azure Monitor or Prometheus for operational visibility
4. **Security**: Always use authentication and enable TLS for production deployments
5. **Resource Limits**: Adjust resource limits based on your specific workload requirements