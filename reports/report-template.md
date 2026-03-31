# Report: YYYY-MM-DD — Title

Periodic synthesis report from accumulated audit findings. Copy this template and save as `reports/YYYY-MM-DD-title.md` when producing a new report.

> **Status:** Draft
> **Audits incorporated:** _list repos included in this synthesis_

## Platform Overview

_What is this platform? What does it do at a high level? Who uses it?_

## Key Findings

### Architecture Summary

_How do the major surfaces relate to each other? What is the high-level data and control flow?_

### Ownership Landscape

_Which teams own which surfaces? Where is ownership clear, and where is it ambiguous?_

### Deployment Topology

_How does code get from repo to production? What are the major deployment paths? Where do they converge or diverge?_

### Dependency Patterns

_What are the most common dependency relationships? Are there unexpected couplings? Circular dependencies?_

## Concerns

### High Priority

_Findings that represent immediate risk or confusion._

- 

### Medium Priority

_Findings that create friction or will become problems over time._

- 

### Low Priority

_Minor issues, cleanup opportunities, or nice-to-haves._

- 

## Source of Truth Conflicts

_Where do multiple repos or configs claim to be the source of truth for the same value?_

| Value / Config | Claimed By | Notes |
|---|---|---|
| | | |

## Coverage Gaps

_Which surfaces or repos have not been audited? Where is understanding still shallow?_

| Surface | Gap | Impact |
|---|---|---|
| | | |

## Recommended Next Steps

1. 
2. 
3. 

## Appendix: Audit Coverage at Time of Report

| Surface | Repos Inventoried | Repos Audited | Notes |
|---|---|---|---|
| | | | |
