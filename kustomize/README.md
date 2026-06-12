# Authorisations Kustomize configuration

Declarative management of Authorisations Kubernetes resources using Kustomize.

## Important usage rule

Do not apply `kustomize/base` directly.

The base manifests are shared building blocks and are intentionally incomplete for standalone deployment (for example, environment-specific selectors, generated secret/config map names, ingress, and other wiring are provided by overlays).

Always apply an overlay such as `kustomize/overlays/uat`.

## File structure

```
kustomize/
├── base/                    # Base configuration (shared)
│   ├── deployment.yaml
│   ├── deployment_hpa.yaml
│   ├── kustomization.yaml
│   └── service.yaml
└── overlays/
    ├── prod/                # Production overlay
    │   ├── deployment_patch.yaml
    │   ├── ingress.yaml
    │   ├── kustomization.yaml
    │   └── ...
    └── uat/                # UAT overlay
        ├── deployment_patch.yaml
        ├── ingress.yaml
        ├── kustomization.yaml
        └── ...
```

## How to use

### 1. Create environment files

Within an overlay directory, create a `.env` file to contain required secret values in the format `KEY=value` (e.g., `overlays/uat/.env`).

**Required values:**

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key-here
DEBUG=False
# ... see backend/.env.template for full list
```

Also create a `.prince2-license` file containing XML license content. This will be mounted in running pods as a ConfigMap during deployment.

### 2. Review configuration

Review the built resource output using `kustomize`:

```bash
# Review UAT configuration
kustomize build kustomize/overlays/uat/ | less

# Do not build/apply base directly
# kustomize build kustomize/base/
```

### 3. Preflight validation

Validate generated manifests before deployment:

```bash
# 1) Ensure overlay builds successfully
kustomize build kustomize/overlays/uat/ > /tmp/authorisations-uat.yaml

# 2) Client-side validation (syntax and basic schema checks)
kubectl apply --dry-run=client --validate=true -f /tmp/authorisations-uat.yaml

# 3) Server-side validation against the target cluster API
kubectl apply --dry-run=server -f /tmp/authorisations-uat.yaml --namespace authorisations
```

### 4. Deploy to Kubernetes

Run `kubectl` with the `-k` flag to generate resources for a given overlay:

```bash
# Dry run
kubectl apply -k kustomize/overlays/uat/ --namespace authorisations --dry-run=server

# Apply
kubectl apply -k kustomize/overlays/uat/ --namespace authorisations
```

## References

- [Kubernetes Kustomize Documentation](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)
- [Kustomize GitHub Repository](https://github.com/kubernetes-sigs/kustomize)
- [Kustomize Examples](https://github.com/kubernetes-sigs/kustomize/tree/master/examples)
