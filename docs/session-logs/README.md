# Session Logs

Session persistence is handled by the AGENT-33 engine memory system rather than static log files.

## How Sessions Are Recorded

The engine automatically captures:
- Conversation history and context
- Decisions made and rationale
- Tool invocations and results
- Workflow execution traces

All session data is stored in PostgreSQL and queryable via the engine API.

## Accessing Session History

```bash
# List recent sessions
agent33 sessions list

# View a specific session
agent33 sessions show <session-id>

# Export session as markdown
agent33 sessions export <session-id> --format md
```

## Session Templates

For manual session documentation, use the templates in `core/workflows/` which define standard formats for session logs and briefings.
