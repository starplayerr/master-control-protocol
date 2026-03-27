# Dependency Matrix Diagram

Visual rendering of the dependency relationships from [maps/dependency-matrix.md](../maps/dependency-matrix.md).

> Update this diagram as the dependency matrix evolves.

```mermaid
graph LR
    subgraph EKS Surface
        eks-cluster[EKS Cluster Config]
        eks-addons[EKS Addons]
        k8s-manifests[K8s Manifests]
    end

    subgraph SageMaker Surface
        sm-pipelines[SageMaker Pipelines]
        model-registry[Model Registry]
    end

    subgraph Jupyter Surface
        jupyter-ext[Jupyter Extension]
        jupyter-hub[JupyterHub Config]
    end

    subgraph SDK Surface
        platform-sdk[Platform SDK]
    end

    subgraph GPU Surface
        gpu-operator[GPU Operator]
        gpu-scheduler[GPU Scheduler]
    end

    subgraph Shared Resources
        ecr[(ECR Registry)]
        param-store[(Parameter Store)]
        secrets-mgr[(Secrets Manager)]
    end

    %% Example dependency relationships — replace with real data
    k8s-manifests --> eks-cluster
    eks-addons --> eks-cluster
    gpu-operator --> eks-cluster
    gpu-scheduler --> gpu-operator
    jupyter-hub --> eks-cluster
    jupyter-ext --> platform-sdk
    sm-pipelines --> model-registry
    sm-pipelines --> platform-sdk

    eks-cluster --> ecr
    sm-pipelines --> ecr
    jupyter-hub --> param-store
    eks-cluster --> secrets-mgr
```

> Replace the example nodes and edges above with actual repos and dependencies discovered through audits.
