# Claudius Maximus - Project Handoff Document

## Project Purpose

**Claudius Maximus** is an AI-powered eDiscovery knowledge base analysis system. It crawls public help documentation from major eDiscovery review platforms (Relativity, Reveal, etc.), generates markdown files for each page, and then processes them through a local LLM to produce exhaustive technical specifications for building a competitive enterprise application.

### Workflow

```
[Public KB Sites] → [Firecrawl] → [Markdown Files] → [Qwen3 via Ollama] → [Narrative Analysis Files]
```

---

## Repository Structure

```
D:\GITHUB\Claudius Maximus\
├── monitor_relevance.py          # Main processing script (watches & processes files)
├── CLAUDE.md                     # This handoff document
├── docs/
│   └── session-logs/             # Session history for continuity
│
├── RELEVANCE PROCESSING ROOM/    # OUTPUT: Processed narrative files
│   ├── narrative_prompt.md       # System prompt for AI analysis
│   ├── processing_state.json     # State persistence (auto-generated)
│   ├── monitor.log               # Processing log
│   └── FIRECRAWL QWEN3 LOCAL/    # Output subfolders (one per source project)
│
├── FIRECRAWL QWEN3 LOCAL*/       # SOURCE: Crawled markdown files (6 folders)
│   └── crawled_data/content/     # Markdown files from crawled sites
│
└── local-agent-orchestrator/     # Supporting repo: Ollama/Docker setup, agents
    ├── docker-compose.yml        # Ollama container config
    ├── orchestrator.py           # Multi-agent orchestration (not used by monitor)
    └── ...
```

---

## How to Run

### Prerequisites

1. **Docker** running with Ollama container:
   ```bash
   cd local-agent-orchestrator
   docker-compose up -d
   ```

2. **Qwen model** pulled:
   ```bash
   docker exec -it <container_id> ollama pull qwen3c-30b-16k:latest
   ```

3. **Ollama API** accessible at `http://localhost:11435`

### Start Processing

```bash
cd "D:\GITHUB\Claudius Maximus"
python monitor_relevance.py
```

The script will:
1. Load/sync state from `processing_state.json`
2. Discover pending files (skip logic happens here, not in AI calls)
3. Process each file through Qwen3
4. Save results to `RELEVANCE PROCESSING ROOM/<project>/`
5. Save state every 10 files
6. Sleep 1 hour between cycles (continuous monitoring mode)

### Stop/Resume

- **Stop**: `Ctrl+C`
- **Resume**: Just run the same command again; state persists

---

## Environment

| Component | Value |
|-----------|-------|
| OS | Windows 11 |
| Python | 3.x |
| Ollama URL | `http://localhost:11435/api/generate` |
| Model | `qwen3c-30b-16k:latest` |
| Context window | 20,000 tokens |
| Timeout | 300 seconds per file |

---

## Key Files

| File | Purpose |
|------|---------|
| `monitor_relevance.py` | Main script - discovers, filters, processes, saves |
| `RELEVANCE PROCESSING ROOM/narrative_prompt.md` | System prompt defining output format |
| `RELEVANCE PROCESSING ROOM/processing_state.json` | Tracks processed files for restart |
| `local-agent-orchestrator/docker-compose.yml` | Ollama container configuration |

---

## Current Status (as of 2026-01-14)

- **Total source files**: 13,734
- **Processed**: ~3,400+ (~25%) - ongoing
- **Remaining**: ~10,300
- **Processing rate**: ~40 seconds/file
- **ETA**: ~115 hours (~5 days)

---

## Known Issues / TODOs

1. Long processing time - consider parallelization or faster model
2. Multiple "Copy" folders may have duplicate content
3. Some files truncated at 16,000 chars - may lose context on very long docs
4. No quality validation on outputs yet

---

## Post-Processing Pipeline (READY)

The 5-stage pipeline transforms raw narratives into actionable phase documents:

```
[13,734 Narratives] → [Parse JSON] → [SQLite Catalog] → [Claude Dedup] → [Dependency Graph] → [Phase Docs]
```

**Location**: `D:\GITHUB\Claudius Maximus\pipeline\`
**Full plan**: See `pipeline/PIPELINE_PLAN.md`

### Pipeline Scripts (All Ready)

| Script | Purpose | Status |
|--------|---------|--------|
| `01_parse_narratives.py` | Parse MD → JSON + Master listings | ✅ READY |
| `02_build_catalog_db.py` | Build SQLite catalog | ✅ READY |
| `03_semantic_dedup.py` | Claude-powered deduplication | ✅ READY |
| `04_dependency_analysis.py` | Build dependency graph | ✅ READY |
| `05_generate_phases.py` | Generate phase documents | ✅ READY |
| `run_pipeline.py` | Orchestration script | ✅ READY |

### Running the Pipeline

```bash
cd "D:\GITHUB\Claudius Maximus\pipeline"

# Test with sample (no Claude API needed)
python run_pipeline.py --sample 50 --skip-dedup

# Full run (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-ant-...
python run_pipeline.py
```

### Pipeline Outputs

```
pipeline/
├── masters/                    # Master listings by section/domain
│   ├── 01_product_strategy/
│   ├── 02_ux_ui/
│   ├── 03_frontend/
│   ├── 04_backend/
│   ├── 05_infrastructure/
│   ├── 06_qa/
│   ├── 07_documentation/
│   ├── 08_roadmap/
│   └── role_views/            # Aggregated views by role
├── data/
│   ├── parsed/                # Individual JSON files
│   ├── feature_catalog.db     # SQLite catalog
│   └── dependency_graph.json  # Feature dependencies
├── phases/                    # Generated phase documents
│   ├── phase_001_*.md
│   ├── phase_002_*.md
│   └── phase_manifest.json
└── reports/                   # Summary reports
```

### End Goal
- 100-200 phase documents, each with 20-30 functionality items
- Dependency-ordered for sequential agent implementation
- Competitive feature parity + innovation differentiation

### Important: No Data Truncation

All pipeline scripts preserve full data throughout. Truncation was removed from:
- Value propositions
- User stories
- Data models
- API endpoints
- UI components
- Test scenarios
- All report tables

---

## Architecture Notes

### Skip Logic (Critical Design Decision)

All skip/resume logic happens **BEFORE** any Ollama API calls:

1. `load_state()` - Load tracked files from JSON
2. `sync_state_with_filesystem()` - Catch files processed but not saved
3. `discover_pending_files()` - Build list of ONLY files needing processing
4. `process_file()` - Called only for pending files

This ensures restart is fast (no AI queries to check status).

### State Persistence

- Saves every 10 files (`save_interval`)
- On crash: lose at most 10 files of progress
- JSON format for easy inspection/debugging
