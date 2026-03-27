# Maps

The maps directory is the platform synthesis layer: the place where individual repo audits become shared architectural understanding.

It contains the cross-cutting analytical artifacts of Master Control Protocol. Rather than focusing on one repo at a time, these files synthesize findings across the ecosystem and turn repo audits into a living operational map of the platform.

This directory is not limited to diagrams. It contains structured analytical documents that explain how the ecosystem fits together, where truth lives, how changes propagate, where information conflicts, what documentation is missing, what assumptions are stale, and where complexity can be reduced.

Taken together, the maps directory functions as a **shared reasoning surface** for the platform.

## Maps

Each file answers a different cross-cutting question:

| Map | Question It Answers |
|---|---|
| [dependency-matrix.md](dependency-matrix.md) | What produces what, and who consumes it? |
| [deployment-flow.md](deployment-flow.md) | How does a code change actually reach production? |
| [source-of-truth.md](source-of-truth.md) | Where does the canonical configuration actually live, and what wins at runtime? |
| [missing-docs.md](missing-docs.md) | What critical knowledge is undocumented or poorly documented? |
| [stale-assumptions.md](stale-assumptions.md) | What appears outdated, abandoned, deprecated, or misleading? |
| [contradictions-and-ambiguities.md](contradictions-and-ambiguities.md) | Where do repos, docs, and team understanding disagree? |
| [candidate-simplifications.md](candidate-simplifications.md) | Where are the best opportunities to reduce complexity and improve the system? |

## How to Update

After completing a repo audit:

1. Read through the audit findings
2. For each finding that is cross-cutting — touches other repos, reveals a platform-level pattern, or contradicts existing maps — update the relevant map
3. Add the source audit in the "Source" column so findings are traceable

Not every audit will produce updates to every map. Update only when there is something meaningful to add.

These files are meant to be updated as new audits are completed, so the maps become a living representation of the platform rather than a one-time architecture snapshot.
