# AGENT-33

Multi-agent orchestration framework — governance layer, evidence capture, session-spanning workflows.

## Repository Structure

- `core/` — Framework specifications, orchestrator rules, research, workflow templates
- `collected/` — Reference architecture from source projects (stubbed for public release)
- `docs/` — AGENT-33 phase planning, competitive analysis, research, session logs
- `engine/` — Runtime engine (FastAPI, workflow executor, LLM routing, memory/RAG, security)
- `scripts/` — Utility scripts

## Engine Quick Start

```bash
cd engine
cp .env.example .env
docker compose up -d
docker compose exec ollama ollama pull llama3.2
curl http://localhost:8000/health
```

See `engine/README.md` for full documentation.

---

## Anti-Corner-Cutting Rules

These rules address a recurring pattern where AI agents silently deliver
shallow versions of planned work that appear complete (tests pass, files exist,
no errors) but don't fulfill the plan's actual intent.

### No Shallow Substitutions

When a plan specifies a deliverable, implement the actual deliverable — not a
superficially similar version that is easier to produce. Both outright omission
and quiet downgrading are forms of skipping. Common substitution patterns:

1. **Shallow tests disguised as real tests.** A plan says "test CRUD
   validation, auth flows, and error paths." The agent writes tests that only
   check routes return 503 or 401 without credentials. These tests verify
   infrastructure configuration, not feature behavior. They would not catch a
   single regression in the actual endpoint logic. **Every test must assert on
   behavior that would catch a real bug in the code under test.**

2. **Placeholder values never resolved.** A plan says "resolve article titles
   from data." The agent sets `title: articleId` with a comment "will be
   resolved by the component" — but no component ever resolves it. The feature
   ships showing raw UUIDs. **If a value needs resolution, the code that
   resolves it must exist in the same PR.**

3. **Direct calls instead of server endpoints.** A plan says "call server API
   for user list." The agent queries the database directly from the client,
   bypassing the server entirely. The server endpoint exists but is never
   called. **If the plan specifies a client-server interaction, both sides must
   be wired together.**

4. **Blocked work silently downgraded.** When a dependency is hard to mock or
   an infrastructure piece is missing, the agent quietly substitutes something
   easier instead of flagging the blocker. **If you cannot implement what the
   plan specifies, say so immediately — do not silently deliver less.**

5. **Asserting on two possible status codes.** Writing
   `assert(status === 503 || status === 401)` means the test doesn't know what
   the code actually does. This is a test that cannot fail and therefore tests
   nothing. **Each assertion must check one specific expected outcome.**

### Proactive Deviation Reporting

Any deviation from the approved plan must be called out **in the same message
where the deviation occurs**. Do not wait for the user to ask "did you cut any
corners?" — that question should never need to be asked. When a gap is created,
immediately include:

- What was specified in the plan
- What was actually delivered and why it differs
- A concrete proposal to close the gap (build mock infrastructure, split into
  follow-up task, etc.)

If you reach the end of implementation and the user has to interrogate you to
discover gaps, the process has failed regardless of whether the gaps are
eventually fixed.

### Test Quality Over Test Count

Test count is not a quality metric. Do not optimize for the number of tests
written. Do not present "X new tests" as evidence of completeness.

- A test that only verifies a route exists or returns a generic error has
  near-zero regression value
- Mock dependencies to reach the actual handler/component logic under test
- Assert on response shapes, validation errors, business rules, and state
  changes
- If mocking infrastructure doesn't exist to test something properly, you must
  either: (a) build the mock infrastructure, or (b) stop and tell the user what
  is missing before writing placeholder tests
- Never silently downgrade test quality
- When reviewing agent-written tests, verify they test what the plan specified,
  not just that they pass

### Pre-Commit Checklist Additions

Add these to your existing pre-commit checklist:

- [ ] New tests exercise real behavior (validation, response shapes, error
      paths) — not just route existence or infrastructure errors
- [ ] Any deviation from the approved plan is called out in the same message
      where it occurs, with a proposal to close the gap
- [ ] No placeholder values shipped unresolved (search for TODOs, hardcoded IDs
      used as display text, comments saying "will be resolved later")
- [ ] If the plan specified client-server wiring, verify the client actually
      calls the server endpoint (not a direct DB query or local mock)
