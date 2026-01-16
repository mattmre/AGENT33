# Agent Routing Map (Model-Agnostic)

Use this map to decide which roles to invoke by task type.

## Role Selection Checklist
- Is the task about scope/priority? Use Director.
- Is the task about sequencing or acceptance criteria? Use Orchestrator.
- Is the task about implementation? Use Worker-Impl.
- Is the task about verification? Use Worker-QA.
- Does a risk trigger apply? Use Reviewer.
- Is it a research/reading task? Use Researcher.
- Is it documentation or templates? Use Documentation.

## Orchestrator
Use when:
- Scoping tasks, defining acceptance criteria, and sequencing work.
- Resolving conflicts or cross-task dependencies.

## Director
Use when:
- Managing multi-repo priorities and scheduling.
- Escalating risks or scope changes.

## Implementer (Worker-Impl)
Use when:
- Writing or modifying code or config files.
- Executing a scoped task with acceptance criteria.

## QA (Worker-QA)
Use when:
- Running tests and verifying outcomes.
- Writing minimal smoke checks if no tests exist.

## Reviewer
Use when:
- Risk triggers apply (security, schema, API, CI/CD).
- A second opinion is needed for design or edge cases.

## Researcher
Use when:
- Gathering context, reading docs, and summarizing constraints.
- Comparing source variants before promotion or merge.

## Documentation
Use when:
- Updating or creating docs, templates, or guides.
- Ensuring doc and code alignment after changes.
