# Deploying StackAI on Kubernetes (Kind)

This guide outlines the steps to deploy the StackAI application (based on the Supabase Docker Compose setup) to a local Kubernetes cluster using Kind.

## Prerequisites

Before you begin, ensure you have the following installed and configured:

- **kubectl**: The Kubernetes command-line tool.
- **Kind**: A tool for running local Kubernetes clusters using Docker container "nodes".
- **Kompose**: A tool to convert Docker Compose files to Kubernetes manifests.
- **Docker**: Docker Desktop or Docker Engine must be installed and running.
- **Azure Container Registry (ACR) Credentials**: Username and password for `stackai.azurecr.io` if you are using private images from this registry.
- **StackAI License Key**: A valid license key for StackAI services.

## Deployment Steps

### Step 1: Create a Kind Cluster

If you don't have a Kind cluster running, create one:

```bash
kind create cluster --name stackai-dev
```

(You can choose any name for your cluster). Set `kubectl` context to this cluster if not set automatically:

```bash
kubectl cluster-info --context kind-stackai-dev
```

### Step 2: Configure Image Pull Secrets (for private ACR)

If your deployment uses private images from `stackai.azurecr.io` (or any other private registry), Kubernetes needs credentials to pull them.

1.  **Delete any old secret (if re-running setup):**

    ```bash
    kubectl delete secret acr-secret --namespace default --ignore-not-found=true
    ```

2.  **Create the Image Pull Secret:**
    Replace `<your_acr_username>` and `<your_acr_password>` with your actual credentials for `stackai.azurecr.io`.

    ```bash
    kubectl create secret docker-registry acr-secret \
      --docker-server=stackai.azurecr.io \
      --docker-username=<your_acr_username> \
      --docker-password=<your_acr_password> \
      --namespace=default
    ```

3.  **Patch the Default Service Account:**
    This allows pods in the `default` namespace to use the secret without specifying it in each deployment.
    ```bash
    kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "acr-secret"}]}' --namespace default
    ```

### Step 3: Configure Application Specifics (e.g., StackAI License)

Critical application configurations, like the `STACKAI_LICENSE`, need to be set. These are typically managed via ConfigMaps or directly as environment variables in the Deployment YAMLs.

1.  **Locate Configuration Target:** Identify which ConfigMap(s) or Deployment(s) require the license key or other essential runtime variables. For example, the `celery-worker` and `stackend` services might expect `STACKAI_LICENSE` in a ConfigMap they reference (e.g., `k8s/stackend--env-configmap.yaml` or similar).
2.  **Update Configuration:**
    - Edit the relevant ConfigMap YAML file (e.g., `k8s/your-service-env-configmap.yaml`).
    - Add or update the `data` section with your license key:
      ```yaml
      data:
        # ... other existing variables ...
        STACKAI_LICENSE: "<your_stackai_license_key>"
      ```
    - Alternatively, if a Deployment expects it directly as an environment variable, edit the Deployment YAML:
      ```yaml
      # ... inside spec.template.spec.containers[].env ...
      - name: STACKAI_LICENSE
        value: "<your_stackai_license_key>"
      ```
3.  **Apply ConfigMap Changes (if any):**
    ```bash
    kubectl apply -f k8s/your-updated-configmap.yaml --namespace default
    ```
    _(Deployments will pick up direct env var changes when they are applied in the next step)._

### Step 4: Deploy the Application

Once manifests are generated, image paths are corrected, secrets are in place, and configurations are updated:

1.  **Navigate to the manifests directory:**
    ```bash
    cd k8s
    ```
2.  **Apply all manifests:**
    ```bash
    kubectl apply -f . --namespace default
    ```
    _(This applies all `_.yaml` files in the current directory).\*

### Step 5: Verify Deployment

Monitor the status of your pods:

```bash
kubectl get pods --namespace default -w
```

Look for pods to reach `Running` or `Completed` state. If pods are stuck in `ImagePullBackOff`, `CrashLoopBackOff`, or `Error`, proceed to the Troubleshooting section.

Check services:

```bash
kubectl get services --namespace default
```

Check logs for a specific pod:

```bash
kubectl logs <pod-name> --namespace default
```

To see previous logs if a pod is restarting:

```bash
kubectl logs <pod-name> --namespace default --previous
```

## Accessing the Application

Once services are running, you'll typically access them via the `kong` API gateway.
From `supabase/docker-compose.yml`, Kong is exposed on `${KONG_HTTP_PORT}` (default often 8000 or a custom port you set in your `.env` for Supabase).

If using Kind, it maps these ports to your `localhost`. You should be able to access StackAI Studio or APIs at `http://localhost:${KONG_HTTP_PORT}`. Check the `SUPABASE_PUBLIC_URL` environment variable used by Studio.

## Troubleshooting / FAQ

**Q: Pods are stuck in `ImagePullBackOff` or `ErrImagePull`.**

- **A1: Incorrect Image Path/Tag:** Double-check the `image:` field in the relevant `Deployment` YAML. Ensure it's the full correct path (e.g., `registry.example.com/myrepo/myimage:tag`) for private images, or the correct public path and tag.
- **A2: Image Pull Secret Issue (Private Registries):**
  - Verify the `acr-secret` (or your secret name) was created correctly with `kubectl create secret docker-registry ...` (not from `~/.docker/config.json` if `credsStore` is used).
  - Ensure the `default` service account (or the specific service account used by the pod) is patched to use this secret: `kubectl get serviceaccount default -o yaml`.
  - Use `kubectl describe pod <pod-name> --namespace default` to see detailed error messages related to image pulling (e.g., `401 Unauthorized`, `not found`).

**Q: Pods are in `CrashLoopBackOff`.**

- **A:** This means the container starts but then exits due to an error.
  - **Check Logs:** The first step is always `kubectl logs <pod-name> --namespace default`. If it crashed, `kubectl logs <pod-name> --namespace default --previous` might show the error from the last run.
  - **Common Causes:**
    - **Application Errors:** Bugs, unhandled exceptions. For StackAI, a missing or invalid `STACKAI_LICENSE` caused `celery-worker` to error out.
    - **Configuration Errors:** Incorrect environment variables, malformed config files. The `db` (PostgreSQL) pod crashed due to errors in `postgresql.conf`.
    - **Dependency Issues:** The application might be trying to connect to another service (like a database) that isn't ready, isn't configured correctly, or is also crashing. Resolve foundational service issues (like `db`) first.
    - **Permissions:** Filesystem permission errors within the container.
    - **Resource Limits:** If very constrained, but less common for startup crashes.

**Q: `db` pod (PostgreSQL / Supabase) fails with `FATAL: configuration file "/etc/postgresql/postgresql.conf" contains errors`.**

- **A:** This indicates a problem with PostgreSQL's main configuration file.
  - In the Supabase setup, custom configurations can be mounted via a PersistentVolumeClaim (PVC) named `db-config` into `/etc/postgresql-custom` within the pod. The image's entrypoint script may then try to incorporate these into the main `postgresql.conf`.
  - If the `db-config` PVC contains malformed configuration snippets, or if the process of merging them fails, the final `postgresql.conf` can become corrupted.
  - Ensure that any custom PostgreSQL configurations intended for the `db-config` volume are correct. If this volume is expected to be initialized by the image or is for specific features like `pgsodium`, ensure it's not pre-populated with conflicting or bad data.
  - As a diagnostic, temporarily removing the `db-config` PVC mount (and the data PVC mount `db-claim8`) from the `db` deployment can help determine if the issue is with the base image or the custom/persistent configuration.

**Q: How was the initial private registry `acr-secret` issue (related to `credsStore: "desktop"` in `~/.docker/config.json`) solved?**

- **A:** When `~/.docker/config.json` uses `credsStore` (common with Docker Desktop), the actual authentication token is not stored directly in the JSON file. Creating a Kubernetes secret using `--from-file=.dockerconfigjson=.../.docker/config.json` will result in a secret that Kubernetes (especially Kind) cannot use to authenticate with the private registry, leading to `401 Unauthorized` errors.
- **The Fix:** Create the secret by explicitly providing the credentials using the `docker-registry` type:
  ```bash
  kubectl create secret docker-registry <secret-name> \
    --docker-server=<your-registry-server> \
    --docker-username=<your-username> \
    --docker-password=<your-password> \
    --namespace=<your-namespace>
  ```
  This embeds the actual credentials into the Kubernetes secret, which the cluster can then use.
