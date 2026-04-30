# TIKNAS Bootstrap

PowerShell scaffolding script for creating the TIKNAS repository on a
Windows machine.

## Context

TIKNAS is the **internal codename** for the enterprise agent
orchestration platform that will launch publicly as **AGENTS33** on
`agents33.com`. The strategic case for splitting it from AGENT33 is
in `../agent33-vs-tiknas-product-split.md`. The integration roadmap
that becomes TIKNAS's founding plan is in
`../opensearch-agent-observability-analysis.md` (rev-2 + rev-3 framing
note).

This bootstrap creates the v0 directory structure, the minimal
scaffolding files, and a first git commit when the target is a fresh
repository. It does **not** create a GitHub remote, does **not**
install anything, and does **not** touch your existing AGENT33
worktree.

## Run on Windows

```powershell
# From any PowerShell window:
cd D:\GITHUB\AGENT33\docs\research\tiknas-bootstrap
.\setup-tiknas-scaffold.ps1
```

That creates `D:\GITHUB\TIKNAS\` with the layout described in the root
TIKNAS `README.md` the script writes.

If your AGENT33 worktree is at a non-default location, pass:

```powershell
.\setup-tiknas-scaffold.ps1 -Agent33Source 'C:\path\to\AGENT33'
```

To target a path other than `D:\GITHUB\TIKNAS`:

```powershell
.\setup-tiknas-scaffold.ps1 -Root 'D:\elsewhere\TIKNAS'
```

To re-run safely on top of an existing scaffold:

```powershell
.\setup-tiknas-scaffold.ps1 -Force
```

## What the script does (one-liner each)

1. Creates `D:\GITHUB\TIKNAS\` (or `-Root`).
2. Writes `README.md`, `LICENSE` (placeholder), `.gitignore`,
   `.gitattributes`, `CHANGELOG.md`.
3. Creates folder skeleton: `core/`, `platform/`, `infrastructure/`,
   `docs/{research,phases,operators}/` with per-folder READMEs.
4. Copies the two founding planning docs from
   `D:\GITHUB\AGENT33\docs\research\` (or `-Agent33Source`) if found.
   Otherwise prints a TODO.
5. `git init`, switches to `main`, stages everything, and makes one
   initial commit when the target is a fresh repository.

## What the script deliberately doesn't do

- No `git push`. No remote.
- No GitHub repo creation.
- No `pip install`, `npm install`, `docker compose`.
- No Phase OS-0 spike infrastructure (that's a later phase).

## Next steps after running

The script prints these too. Summary:

1. Review the imported planning docs in `D:\GITHUB\TIKNAS\docs\research\`.
2. Answer the ten gating questions in
   `agent33-vs-tiknas-product-split.md` §10.
3. Decide on Path X / Y / Z (OpenSearch / Langfuse+Dify / compose).
4. Run Phase OS-0 decision spike when ready.
5. Decide whether and when to create the GitHub remote.

## Caveats

- The planning doc import depends on you having the
  `claude/plan-analysis-tool-yAI8I` branch fetched in your AGENT33
  worktree, since that's where the draft planning docs currently live.
  If the branch isn't there yet, the script falls back to a manual TODO
  message.
- The looped agent on the other machine doesn't know about this split
  yet. Coordinate with it before the TIKNAS GitHub remote is created
  so it doesn't keep landing AGENT33-as-monolith commits unaware.
