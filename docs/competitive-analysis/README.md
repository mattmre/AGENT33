# Competitive Analysis Index

This folder contains comparative analyses of external agent orchestration frameworks, configurations, and tooling against AGENT-33's capabilities. The goal is to identify features, patterns, and approaches that can enhance our orchestration framework.

## Purpose

1. **Identify Best Practices**: Learn from mature implementations in the ecosystem
2. **Gap Analysis**: Find capabilities AGENT-33 lacks that would add value
3. **Pattern Discovery**: Discover workflow patterns worth adopting
4. **Competitive Positioning**: Understand where AGENT-33 excels and where it can improve
5. **Roadmap Input**: Generate backlog items from analysis findings

## Analysis Methodology

Each analysis follows this structure:

1. **Repository Overview**: Purpose, structure, and philosophy
2. **Feature Inventory**: Complete cataloging of capabilities
3. **Comparative Analysis**: Side-by-side with AGENT-33
4. **Gap Identification**: What we're missing
5. **Recommendations**: Actionable items with priority
6. **Integration Opportunities**: What can be directly incorporated

## Analyses Completed

| Date | Repository | Status | Key Findings |
|------|------------|--------|--------------|
| 2026-01-20 | [dagster-io/dagster](competitive-analysis-dagster-2026-01-20.md) | Complete | Asset-first definitions; declarative automation; freshness policies; lineage graphs; partitioning; 12 backlog items generated (CA-020 to CA-031) |
| 2026-01-20 | [affaan-m/everything-claude-code](2026-01-20_everything-claude-code.md) | Complete | Production-ready configs; hooks system; modular rules; TDD workflow |

## Analyses Planned

| Repository | Priority | Reason |
|------------|----------|--------|
| TBD | - | - |

## How to Use This Resource

### For Planning
- Review analyses before major feature work
- Check recommendations for quick wins
- Use gap analysis for roadmap prioritization

### For Implementation
- Reference external examples for patterns
- Adapt configurations to AGENT-33 conventions
- Validate adoptions against our model-agnostic principle

### For Contributing
1. Select a target repository for analysis
2. Create a new file: `YYYY-MM-DD_<repo-name>.md`
3. Follow the analysis template structure
4. Update this index with the new entry
5. Add any backlog items to `core/arch/backlog-index.md`

## Analysis Template

```markdown
# Competitive Analysis: <Repository Name>

**Date**: YYYY-MM-DD
**Repository**: <GitHub URL>
**Analyst**: <Agent/Human>
**Status**: Draft | Complete

## Executive Summary
<2-3 paragraphs summarizing findings>

## Repository Overview
### Purpose
### Structure
### Philosophy

## Feature Inventory
<Complete list of capabilities>

## Comparative Analysis
<Side-by-side with AGENT-33>

## Gap Analysis
<What AGENT-33 is missing>

## Recommendations
<Prioritized action items>

## Integration Opportunities
<What can be directly adopted>

## References
<Links and citations>
```

---

**Last Updated**: 2026-01-20
