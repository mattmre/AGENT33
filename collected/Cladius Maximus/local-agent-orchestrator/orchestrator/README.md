# Orchestrator Documentation

This directory contains all the orchestrator-related documentation for coordinating the multi-agent system.

## Files and Directories

- **PROMPT_PACK.md** - Reusable prompts for agents
- **agents/** - Agent configuration files and roles
- **handoff/** - Handoff procedures and coordination
- **runbooks/** - Operational runbooks for workflows

## System Overview

The orchestrator coordinates between Claude (planning and review) and Qwen (implementation) agents. The system uses documentation files as the single source of truth:

1. **PLAN.md** - High-level goals, constraints, and acceptance criteria
2. **TASKS.md** - Task queue with status updates
3. **STATUS.md** - Current repository state snapshot
4. **DECISIONS.md** - Design decisions record

## Coordination Process

1. Orchestrator updates PLAN + TASKS
2. Workers pick a task, make a branch, implement, run tests, open PR / provide diff
3. Orchestrator reviews and merges