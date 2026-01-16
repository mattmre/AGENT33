# C# instructions

```yaml
applyTo:
  - "**/*.cs"
  - "EDCTool/**"
```
- Target `.NET Framework 4.8`; do **not** convert to SDK‑style.
- Keep UI thread responsive; offload heavy IO to background tasks.
- Strict logging: include counters (files, pages, exports), timings, and destinations.
- Provide CLI or config sections for paths and options when possible.
