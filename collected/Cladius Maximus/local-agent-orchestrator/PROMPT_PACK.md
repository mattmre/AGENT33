# Prompt Pack

Reusable prompts for agents working in this system.

## System Overview
You are working with a local agent orchestration system that coordinates between Claude (planning/review) and Qwen (implementation) agents using documentation files as the single source of truth.

## Agent Coordination Rules
- Follow PLAN.md for project goals
- Work from TASKS.md for task queue
- Update documentation as you work
- Return results with clear explanations

## Key Instructions for Implementation

1. Make the smallest change that meets acceptance criteria
2. Focus on correctness over code style
3. Use documentation as the single source of truth
4. Provide clear explanations of changes
5. Update status regularly