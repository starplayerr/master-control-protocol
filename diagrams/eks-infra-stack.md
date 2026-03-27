# EKS InfraStack Diagram

Architecture of the EKS infrastructure layer and its relationships.

> Update this diagram as EKS-related audits reveal the actual topology.

```mermaid
graph TD
    subgraph AWS Account
        subgraph VPC
            subgraph EKS Cluster
                cp[Control Plane]

                subgraph Node Groups
                    ng-general[General Node Group]
                    ng-gpu[GPU Node Group]
                    ng-system[System Node Group]
                end

                subgraph Namespaces
                    ns-platform[platform]
                    ns-ml[ml-workloads]
                    ns-jupyter[jupyter]
                    ns-monitoring[monitoring]
                    ns-system[kube-system]
                end
            end

            alb[ALB / Ingress]
            nat[NAT Gateway]
        end

        ecr[(ECR)]
        s3[(S3)]
        sm[SageMaker]
        param[(Parameter Store)]
        secrets[(Secrets Manager)]
        iam[IAM Roles]
    end

    cp --> ng-general
    cp --> ng-gpu
    cp --> ng-system

    alb --> ns-platform
    alb --> ns-jupyter

    ns-ml --> sm
    ns-platform --> ecr
    ns-platform --> s3
    ns-jupyter --> param
    ng-gpu --> ns-ml

    ns-system --> secrets
    iam -.->|IRSA| ns-platform
    iam -.->|IRSA| ns-ml
    iam -.->|IRSA| ns-jupyter
```

> Replace placeholder namespaces, node groups, and connections with actual infrastructure as discovered through audits.
