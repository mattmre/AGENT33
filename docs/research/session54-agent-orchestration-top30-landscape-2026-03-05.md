# Session 54 Research — Agent Orchestration Top-30 Landscape (2026-03-05)

## Scope and Method

- Query used: `"orchestration framework" "agent"` (GitHub, sort by stars desc)
- Top-30 candidate set captured in session SQL table: `agent_orchestration_repos`
- Explicit requirement satisfied: `deepset-ai/haystack` included
- This report captures the ranked landscape and extraction notes used for AGENT-33 ingestion planning

## Top-30 Snapshot

| Rank | Repository | Stars | URL |
| ---: | --- | ---: | --- |
| 1 | deepset-ai/haystack | 24397 | https://github.com/deepset-ai/haystack |
| 2 | kyegomez/swarms | 5830 | https://github.com/kyegomez/swarms |
| 3 | VRSEN/agency-swarm | 4023 | https://github.com/VRSEN/agency-swarm |
| 4 | Kocoro-lab/Shannon | 1142 | https://github.com/Kocoro-lab/Shannon |
| 5 | dynamiq-ai/dynamiq | 1032 | https://github.com/dynamiq-ai/dynamiq |
| 6 | Dicklesworthstone/claude_code_agent_farm | 675 | https://github.com/Dicklesworthstone/claude_code_agent_farm |
| 7 | christopherkarani/Swarm | 374 | https://github.com/christopherkarani/Swarm |
| 8 | foreveryh/mentis | 294 | https://github.com/foreveryh/mentis |
| 9 | manthanguptaa/water | 238 | https://github.com/manthanguptaa/water |
| 10 | The-Swarm-Corporation/swarms-rs | 129 | https://github.com/The-Swarm-Corporation/swarms-rs |
| 11 | marketagents-ai/MarketAgents | 113 | https://github.com/marketagents-ai/MarketAgents |
| 12 | gannonh/kata-orchestrator | 97 | https://github.com/gannonh/kata-orchestrator |
| 13 | dsifry/metaswarm | 94 | https://github.com/dsifry/metaswarm |
| 14 | bijutharakan/multi-agent-squad | 79 | https://github.com/bijutharakan/multi-agent-squad |
| 15 | Snowflake-Labs/orchestration-framework | 70 | https://github.com/Snowflake-Labs/orchestration-framework |
| 16 | 0xstely/nexus-agents | 60 | https://github.com/0xstely/nexus-agents |
| 17 | martymcenroe/AssemblyZero | 55 | https://github.com/martymcenroe/AssemblyZero |
| 18 | nshkrdotcom/synapse | 39 | https://github.com/nshkrdotcom/synapse |
| 19 | boris-dotv/fintalk.v | 39 | https://github.com/boris-dotv/fintalk.v |
| 20 | tripolskypetr/agent-swarm-kit | 33 | https://github.com/tripolskypetr/agent-swarm-kit |
| 21 | mubaidr/gem-team | 30 | https://github.com/mubaidr/gem-team |
| 22 | bsamud/openfoundry-agentic-framework | 30 | https://github.com/bsamud/openfoundry-agentic-framework |
| 23 | ShunsukeHayashi/context_engineering_MCP | 28 | https://github.com/ShunsukeHayashi/context_engineering_MCP |
| 24 | Percena/AgentScale | 27 | https://github.com/Percena/AgentScale |
| 25 | yx-fan/multi-agent-orchestration-framework | 26 | https://github.com/yx-fan/multi-agent-orchestration-framework |
| 26 | zeynepyorulmaz/openclaw-orchestrator | 23 | https://github.com/zeynepyorulmaz/openclaw-orchestrator |
| 27 | jonnyzzz/run-agent | 21 | https://github.com/jonnyzzz/run-agent |
| 28 | Unfold-Security/pydantic-collab | 20 | https://github.com/Unfold-Security/pydantic-collab |
| 29 | hfahrudin/orkes | 18 | https://github.com/hfahrudin/orkes |
| 30 | Zaious/ChronicleCore-Architecture | 17 | https://github.com/Zaious/ChronicleCore-Architecture |

## Top-10 Capability Extraction Notes

1. **deepset-ai/haystack**: componentized orchestration + modular pipeline composition + strong retrieval/eval ecosystem.
2. **kyegomez/swarms**: multi-agent orchestration patterns and role delegation emphasis.
3. **VRSEN/agency-swarm**: reliability-oriented multi-agent orchestration envelope.
4. **Kocoro-lab/Shannon**: production-oriented orchestration framing.
5. **dynamiq-ai/dynamiq**: workflow-centric agentic orchestration architecture.
6. **claude_code_agent_farm**: high parallel-agent fanout and coding-agent coordination.
7. **christopherkarani/Swarm**: lightweight orchestration runtime footprint.
8. **foreveryh/mentis**: LangGraph-based multi-agent graph orchestration.
9. **manthanguptaa/water**: framework-agnostic orchestration layer pattern.
10. **swarms-rs**: Rust-oriented orchestration runtime patterns for reliability/perf.

## Explicit Haystack Inclusion

`deepset-ai/haystack` is ranked #1 in this capture and is included as a core benchmark for:

- Modular orchestration component design
- Retrieval + generation workflow composition
- Production-oriented RAG and evaluation practices

## Output to Ingestion Pipeline

This ranked set is now wired into AGENT-33 ingestion work via:

- `POST /v1/improvements/intakes/competitive/repos` (batch competitive intake creation)
- `POST /v1/improvements/feature-candidates/score` (feature-candidate scoring/prioritization)

