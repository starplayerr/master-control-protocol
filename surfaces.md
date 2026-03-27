# Surfaces

Surfaces are major functional domains of the platform. Each surface groups related repositories by the area of the system they serve, rather than by individual repo boundaries.

Organizing by surface helps answer: "If I need to change something about _X_, which repos are involved?"

## Surface Template

Each surface can include:

- **Name** — short identifier
- **Description** — what this area of the platform does
- **Key Repos** — the repositories that implement this surface
- **Scope** — what is in and out of scope for this surface
- **Last Updated** — when this surface definition was last reviewed

---

## EKS

**Description:** Kubernetes cluster infrastructure, deployment targets, networking, and cluster-level configuration.

**Key Repos:**
- _example-eks-cluster_
- _example-eks-addons_
- _example-k8s-manifests_

**Scope:** Cluster provisioning, node groups, networking, ingress, service mesh, cluster-level RBAC, Helm charts.

**Last Updated:** —

---

## SageMaker

**Description:** Machine learning training and inference infrastructure, pipeline orchestration, model management.

**Key Repos:**
- _example-sagemaker-pipelines_
- _example-model-registry_

**Scope:** Training jobs, endpoints, pipeline definitions, model artifacts, feature store integrations.

**Last Updated:** —

---

## Jupyter

**Description:** Jupyter notebook environments, custom extensions, and the extension ecosystem for interactive compute.

**Key Repos:**
- _example-jupyter-extension_
- _example-jupyter-hub-config_

**Scope:** JupyterHub deployment, server extensions, lab extensions, kernel management, user environment configuration.

**Last Updated:** —

---

## SDK

**Description:** Internal SDK(s) used by other services and teams to interact with the platform.

**Key Repos:**
- _example-platform-sdk_

**Scope:** Client libraries, API wrappers, auth helpers, configuration utilities.

**Last Updated:** —

---

## GPU Management

**Description:** GPU allocation, scheduling, quota management, and device plugin configuration.

**Key Repos:**
- _example-gpu-operator_
- _example-gpu-scheduler_

**Scope:** GPU device plugins, scheduling policies, quota enforcement, monitoring, node labeling.

**Last Updated:** —

---

> Replace the italic example repos above with real repositories as you populate the inventory.
>
> Add new surfaces as the platform map expands. Surfaces are not fixed — they should evolve as understanding deepens.
