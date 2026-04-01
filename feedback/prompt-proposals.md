---
title: "Prompt Evolution Proposals"
role: template
last_updated: 2026-04-01
depends_on:
  - feedback/capture-log.jsonl
freshness: current
scope: platform
---

# Prompt Evolution Proposals (2026-04-01)

Auto-generated from post-audit feedback. Each proposal needs human review
before being applied to prompt templates.

## prompts/library.md

### Proposal 1: Missing field: tech_stack.frameworks
**Based on:** 1 prompt-gap captures across audits/python-build-standalone.md
**Gap:** Field 'tech_stack.frameworks' is 'unknown' — prompt may not have extracted this
**Suggested addition to prompt:**
> Ensure the prompt explicitly asks about frameworks and provides guidance on where to find it in the repo.
**Status:** Pending review
