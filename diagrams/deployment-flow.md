# Deployment Flow Diagram

Visual rendering of how code moves from repos to production, sourced from [maps/deployment-flow.md](../maps/deployment-flow.md).

> Update this diagram as deployment paths are discovered and documented.

```mermaid
flowchart LR
    subgraph Repos
        A[Repo A]
        B[Repo B]
        C[Repo C]
    end

    subgraph CI
        jenkins[Jenkins]
        gh-actions[GitHub Actions]
    end

    subgraph Artifacts
        ecr[(ECR)]
        s3[(S3)]
    end

    subgraph CD
        spinnaker[Spinnaker]
        argocd[ArgoCD]
    end

    subgraph Targets
        eks[EKS Cluster]
        sagemaker[SageMaker]
        lambda[Lambda]
    end

    A --> jenkins --> ecr --> spinnaker --> eks
    B --> gh-actions --> ecr --> argocd --> eks
    C --> gh-actions --> s3 --> sagemaker
```

> Replace the example paths above with actual deployment flows discovered through audits.

## Branch-to-Environment Flow

```mermaid
flowchart TD
    feature[Feature Branch] -->|PR merge| main[main / master]
    main -->|CI build| artifact[Build Artifact]
    artifact -->|auto-deploy| staging[Staging]
    staging -->|manual promotion| prod[Production]

    main -.->|some repos| prod
    feature -.->|some repos deploy from feature| staging
```

> Not all repos follow the same promotion model. Document exceptions in [maps/deployment-flow.md](../maps/deployment-flow.md).
