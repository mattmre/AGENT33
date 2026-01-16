# System-Level Coding Rules

This document outlines the general coding rules and constraints that all agents must follow when working with the local agent orchestration system.

## Core Principles

### 1. Single Source of Truth
All system state is maintained in documentation files:
- PLAN.md for goals and acceptance criteria
- TASKS.md for task queue and status
- STATUS.md for current repository state
- DECISIONS.md for design decisions

### 2. Minimal Changes
- Make the smallest change that meets acceptance criteria
- Avoid unnecessary refactoring or over-engineering
- Focus on functionality over aesthetics

### 3. Documentation-First Approach
- Update documentation files before and after changes
- All documentation must be kept in sync with code
- Clear, concise descriptions of changes and reasoning

## Technical Constraints

### 4. Local Development
- All development occurs locally with Ollama setup
- No cloud-based LLM dependencies
- Resources limited to available hardware
- Use of Docker container for consistent environments

### 5. GPU Resource Management
- Limited to one parallel model load (OLLAMA_NUM_PARALLEL=1)
- Queue size set to 256 (OLLAMA_MAX_QUEUE=256)
- Optimized memory usage with q8_0 cache type
- Flash attention enabled for performance

### 6. Context Management
- Working with 16K context window
- Manage memory limits in models
- Handle long context properly without overflow

## Execution Workflow Rules

### 7. Task Management
- Tasks are picked from TASKS.md queue
- Each task has explicit acceptance criteria
- Status updates are made in TASKS.md
- Branch names follow pattern: `ask/T#-short-name`

### 8. Implementation Requirements
- Output commands, unified diffs, and test results
- Provide clear explanations of what was done and why
- Focus on correctness over code style
- Keep changes focused and targeted

### 9. Testing Standards
- Run tests after implementation
- Ensure results are provided to orchestrator
- Verify that changes don't break existing functionality
- Address any failing tests

## Inter-Agent Communication

### 10. Coordination with Orchestrator
- Follow orchestrator's PLAN.md for project goals
- Adhere to TASKS.md for task prioritization
- Return diff results and test outputs clearly
- Request clarification on acceptance criteria when needed

### 11. Status Updates
- Update TASKS.md regularly with progress
- Provide clear status messages in task records
- Indicate when tasks are complete or blocked
- Communicate any challenges or roadblocks clearly

## Quality Standards

### 12. Change Quality
- Maintain backward compatibility
- Follow existing code patterns
- Keep implementation simple and clear
- Avoid introducing new bugs

### 13. Documentation Quality
- All changes must be documented
- Updates to system documentation must be accurate
- Use clear and consistent terminology
- Review documentation for correctness after changes

## Special Considerations

### 14. Ollama-Specific Rules
- Configure OLLAMA_NUM_PARALLEL=1 for 30B models
- Use OLLAMA_MAX_LOADED_MODELS=1 to limit memory
- Set OLLAMA_KV_CACHE_TYPE=q8_0 for VRAM efficiency
- Enable OLLAMA_FLASH_ATTENTION=1 for faster processing
- Set OLLAMA_KEEP_ALIVE=30m for persistence

### 15. Windows Environment
- Use PowerShell scripts (.ps1) for local execution
- Follow Windows path conventions
- Account for Windows-specific limitations and quirks
- Ensure PowerShell execution policies allow script execution

## Reference

This system should maintain the principles from the following documents:
- WORKER_RULES.md - specific worker behavior rules
- PROMPT_PACK.md - reusable prompts for agents
- DECISIONS.md - design decisions record