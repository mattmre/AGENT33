# AGENTS.md (EDCwayback)

## Project Status
Transforming EDCwayback into a forensic web archive collection platform.
- **Current Phase**: 1.1 Configuration Management (75% complete)
- **Next Phase**: 1.2 Database Layer

## Allowed
- Parser/refactor of Wayback client code.
- Add retries/backoff, structured logging, and CLI flags.
- Expand tests and fixtures.
- Configuration system enhancements (schema, loader, CLI integration).
- Database layer implementation (SQLAlchemy models, Alembic migrations).
- Forensic features (chain of custody, hashing, audit logging).

## Needs approval
- New external services or dependencies.
- Changes to file formats produced (CSV/JSON schemas).
- Database schema changes after initial implementation.
- Security-sensitive changes (encryption, authentication).

## PR requirements
- Include before/after CLI examples, test summary, and sample outputs.
- If rate limits are touched, explain backoff math and defaults.
- For config changes, show example YAML and env var mappings.
- For database changes, include migration scripts.

## Key Documentation
- `docs/sessions/` - Session logs tracking development progress
- `docs/phases/` - Detailed phase specifications
- `docs/architecture/development-phases.md` - Full 45-phase roadmap
- `.claude/CLAUDE.md` - Project context for AI assistants
