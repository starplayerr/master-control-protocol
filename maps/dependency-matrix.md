# Dependency Matrix

How repos produce and consume each other's outputs. This maps the ecosystem in terms of artifact flow, not just repo ownership. The goal is to show what each repo produces, who consumes it, and what kind of dependency exists between them.

See also: [diagrams/dependency-matrix.md](../diagrams/dependency-matrix.md) for a visual rendering.

---

## Library / Package Flows

Reusable code published to package registries and consumed by other repos or baked into containers.

This section helps answer:

- What reusable code is published?
- Where is it consumed?
- Are dependency chains obvious or hidden?

| Producer | Package | Registry | Consumer(s) | Version Pinning | Notes | Source |
|---|---|---|---|---|---|---|
| | | | | | | |

---

## Container Image Flows

Which repos produce container images and which downstream systems, repos, or deployment layers consume those images.

This section helps clarify:

- Image producers and consumers
- Image dependency boundaries
- Where deployment coupling exists

| Producer | Image | Registry | Consumer(s) | Tag Strategy | Notes | Source |
|---|---|---|---|---|---|---|
| | | | | | | |

---

## Infrastructure Flows

Infrastructure-level relationships, including confirmed apply order from remote state references or other infra coupling mechanisms.

This section helps show:

- Which infra layers depend on earlier ones
- How state or outputs are passed
- What must exist before something else can deploy

| Producer | Output | Consumer | Coupling Mechanism | Notes | Source |
|---|---|---|---|---|---|
| | | | | | |

---

## Dependency Matrix Table

Normalized view of all dependency relationships across the platform.

| Producer | Artifact | Consumer | Link Type | Notes | Source |
|---|---|---|---|---|---|
| | | | | | |

**Link type values:** `library` · `container image` · `remote state` · `API call` · `shared config` · `data pipeline` · `infra output` · `other`

---

## Unexpected or Concerning Dependencies

Dependencies that seem wrong, unnecessary, circular, or that create fragile coupling.

| Dependency | Concern | Discovered In | Notes |
|---|---|---|---|
| | | | |
