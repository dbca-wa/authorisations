# Deployment Guide

This document describes how to deploy the Authorisations application to Kubernetes using Kustomize.

## Overview

Kubernetes manifests for Authorisations are managed under `kustomize/` using a base + overlays structure.

## Important usage rule

Do not apply `kustomize/base` directly.

The base manifests are shared building blocks and are intentionally incomplete for standalone deployment (for example, environment-specific selectors, generated secret/config map names, ingress, and other wiring are provided by overlays).

**Always apply an overlay such as `kustomize/overlays/uat` or `kustomize/overlays/prod`.**

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

## Environment configuration

### Create environment files

Within an overlay directory, create a `.env` file to contain required secret values in the format `KEY=value` (e.g., `overlays/uat/.env`).

**Required values:**

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key-here
DEBUG=False
# ... see backend/.env.template for full list
```

Also create a `.prince-license` file containing XML license content. This will be mounted in running pods as a ConfigMap during deployment. The file is renamed to `license.dat` in the ConfigMap key and on the mounted filesystem.

## Maintenance mode

The application supports a maintenance mode for safe deployments and database migrations without displaying server errors to users.

Set the `MAINTAINANCE_MODE` environment variable to `True`:

```bash
MAINTAINANCE_MODE=True
```

When enabled:
- All users (including authenticated reviewers) see a user-friendly "Under Maintenance" page
- API endpoints return HTTP 503 Service Unavailable with JSON response
- File downloads (applications and attachments) are blocked
- No database queries are performed to serve the maintenance page

### Typical workflow

1. **Before deployment or migration:** Enable maintenance mode by redeploying with `MAINTAINANCE_MODE=True`
2. **Perform safe operations:** Deploy changes, run database migrations, restart services
3. **After deployment:** Disable maintenance mode by redeploying with `MAINTAINANCE_MODE=False` or removing the environment variable (preferred)


## Review configuration

Review the built resource output using `kustomize`:

```bash
# Review UAT configuration
kustomize build kustomize/overlays/uat/ | less

# Review production configuration
kustomize build kustomize/overlays/prod/ | less
```

## Preflight validation

Validate generated manifests before deployment.

### UAT

```bash
# 1) Ensure overlay builds successfully
kustomize build kustomize/overlays/uat/ > /tmp/authorisations-uat.yaml

# 2) Client-side validation (syntax and basic schema checks)
kubectl apply -f /tmp/authorisations-uat.yaml --namespace=authorisations --dry-run=client --validate=true

# 3) Server-side validation against the target cluster API
kubectl apply -f /tmp/authorisations-uat.yaml --namespace=authorisations --dry-run=server
```

### Production

```bash
# 1) Ensure overlay builds successfully
kustomize build kustomize/overlays/prod/ > /tmp/authorisations-prod.yaml

# 2) Client-side validation (syntax and basic schema checks)
kubectl apply -f /tmp/authorisations-prod.yaml --namespace=authorisations --dry-run=client --validate=true

# 3) Server-side validation against the target cluster API
kubectl apply -f /tmp/authorisations-prod.yaml --namespace=authorisations --dry-run=server
```

## Deploy to Kubernetes

Run `kubectl` with the `-k` flag to generate resources for a given overlay.

### UAT

```bash
# Verify you are connected to UAT
kubectl config current-context

# or switch context if needed
kubectl config use-context uat

# Dry run
kubectl apply -k kustomize/overlays/uat/ --namespace=authorisations --dry-run=server

# Switch to maintenance mode if needed
kubectl set env deployment/authorisations-uat MAINTAINANCE_MODE=True --namespace=authorisations

# Apply
kubectl apply -k kustomize/overlays/uat/ --namespace=authorisations

# Disable maintenance mode after deployment
kubectl set env deployment/authorisations-uat MAINTAINANCE_MODE- --namespace=authorisations
```

### Production

**Ensure you are connected to the correct production cluster context before running these commands.**

```bash
# Verify you are connected to production
kubectl config current-context

# or switch context if needed
kubectl config use-context PRODUCTION!

# Dry run
kubectl apply -k kustomize/overlays/prod/ --namespace=authorisations --dry-run=server

# Switch to maintenance mode if needed
kubectl set env deployment/authorisations-prod MAINTAINANCE_MODE=True --namespace=authorisations

# Apply
kubectl apply -k kustomize/overlays/prod/ --namespace=authorisations

# Disable maintenance mode after deployment
kubectl set env deployment/authorisations-prod MAINTAINANCE_MODE- --namespace=authorisations
```

## Verify deployment

Run the following command to check the rollout status of the deployment:

```bash
# UAT
kubectl rollout status deployment/authorisations-uat --namespace=authorisations

# Production
kubectl rollout status deployment/authorisations-prod --namespace=authorisations
```

## References

- [Kubernetes Kustomize Documentation](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/)
- [Kustomize GitHub Repository](https://github.com/kubernetes-sigs/kustomize)
- [Kustomize Examples](https://github.com/kubernetes-sigs/kustomize/tree/master/examples)

---

**See [README.md](README.md) for the documentation index.**
