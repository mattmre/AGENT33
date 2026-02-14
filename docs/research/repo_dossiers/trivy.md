# Repo Dossier: aquasecurity/trivy

**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

Trivy is Aqua Security's open-source, comprehensive security scanner written in Go, designed for DevSecOps teams who need to find vulnerabilities, misconfigurations, secrets, SBOM data, and license violations across container images, filesystems, Git repositories, Kubernetes clusters, and cloud infrastructure (AWS). Its primary interface is a CLI (`trivy image`, `trivy fs`, `trivy k8s`, `trivy aws`, etc.) with additional deployment modes as a server (client-server architecture for centralized DB), a Kubernetes operator (Trivy Operator), and GitHub Actions integration (`aquasecurity/trivy-action`). The core orchestration primitive is a **scanner pipeline**: target parsing produces an artifact representation, which is fed through parallel scanner modules (vulnerability, misconfiguration, secret, license, SBOM), each backed by dedicated vulnerability databases (trivy-db, trivy-java-db, trivy-checks), and results are aggregated, filtered by severity/policy, and emitted in configurable output formats (table, JSON, SARIF, CycloneDX, SPDX, GitHub template, etc.). With 24,000+ GitHub stars (as of early 2026), it is the most widely adopted open-source vulnerability scanner and is the default scanner in Harbor registry, GitLab CI, Artifact Hub, and many enterprise CI/CD pipelines.

## 2) Core orchestration model

- **Primary primitive:** Scanner pipeline. Each invocation runs a linear pipeline: (1) artifact analysis (OS detection, package extraction, config parsing) -> (2) parallel scanner execution (vuln, misconfig, secret, license) -> (3) result aggregation -> (4) filtering/policy -> (5) output formatting. Not a graph, DAG, or agent system -- it is a deterministic multi-scanner pipeline.
- **State model:** Stateless per scan. No persistent state between invocations. The vulnerability databases (trivy-db, trivy-java-db) are downloaded/cached locally (`~/.cache/trivy/`) and refreshed periodically. The Trivy server mode keeps the DB in memory for faster client queries but does not maintain scan state.
- **Concurrency:** Parallel scanner execution within a single scan (vulnerability + misconfiguration + secret scanners run concurrently on the same artifact). The `--parallel` flag controls concurrency for Kubernetes scanning (multiple resources scanned in parallel). Go goroutines handle concurrency internally.
- **Human-in-the-loop:** No interactive mode. Policy enforcement via `--exit-code` (non-zero exit on findings), `--severity` filtering, `.trivyignore` suppression files, and Rego/OPA policy files. CI/CD pipelines use exit codes to gate PRs. Trivy Operator provides Kubernetes admission controller webhooks for automated enforcement.

## 3) Tooling and execution

- **Tool interface:** CLI binary with subcommands (`trivy image`, `trivy fs`, `trivy repo`, `trivy config`, `trivy k8s`, `trivy aws`, `trivy sbom`, `trivy rootfs`, `trivy vm`, `trivy plugin`). Plugin system for extending scanners. Client-server mode via `trivy server` (gRPC) and `trivy client`. GitHub Action wrapper (`aquasecurity/trivy-action`). Go library importable as SDK for programmatic use (`github.com/aquasecurity/trivy/pkg`).
- **Runtime environment:** Runs locally as a single binary (no dependencies), in Docker containers, in CI/CD (GitHub Actions, GitLab CI, Jenkins, CircleCI, etc.), as a Kubernetes operator (Trivy Operator for continuous cluster scanning), and in server mode for centralized deployment. The trivy-action GitHub Action uses the containerized Trivy binary.
- **Sandboxing / safety controls:** Trivy is a read-only scanner -- it never modifies the scanned target. For misconfiguration scanning, it uses embedded Rego policies (trivy-checks) that evaluate configuration files without executing them. Secret scanning uses regex patterns against file content. No code execution occurs during scanning. The scanner itself is supply-chain-hardened: signed releases, SBOM published for Trivy itself, reproducible builds, and Cosign signatures on container images.

## 4) Observability and evaluation

- **Tracing/logging:** Debug logging via `--debug` flag. Structured JSON output via `--format json`. SARIF output for GitHub Security tab integration (`--format sarif`). Cache debugging via `--cache-dir` inspection. The `--list-all-pkgs` flag includes full package inventory in output for audit trails. Server mode exposes Prometheus metrics endpoint. No OpenTelemetry integration natively.
- **Evaluation harness:** Trivy maintains an extensive test suite with: (1) unit tests per scanner module, (2) integration tests against real container images (golden files for expected vulnerability counts), (3) the `trivy-db` feed has its own validation pipeline ensuring advisory data integrity. The community benchmarks Trivy against competing scanners (Grype, Snyk, Clair) on detection accuracy using the `vulndb-fixtures` test dataset. No formal SWE-bench equivalent, but the Aqua Vulnerability Database (AVD) provides human-curated ground truth for CVE detection accuracy.

## 5) Extensibility

- **Where extensions live:** Plugins in `~/.trivy/plugins/` directory. Custom Rego policies in user-specified directories. VEX (Vulnerability Exploitability eXchange) documents for contextual suppression. Custom output templates via Go `text/template`.
- **How to add tools/skills:** (1) **Plugins**: `trivy plugin install <git-repo>` installs Go/Python/Shell plugins that extend scanner capabilities. Plugins run as subprocesses and receive scan results via stdin/stdout. (2) **Custom policies**: Write Rego `.rego` files, place in a directory, pass via `--policy <dir>`. Policies can check any configuration attribute. (3) **Custom templates**: Go template files for custom output formatting, passed via `--template @<file>`. (4) **VEX documents**: OpenVEX or CSAF format documents to suppress/annotate findings contextually. (5) **Module system**: Internal analyzer/scanner modules can be added by implementing Go interfaces (`Analyzer`, `Scanner`).
- **Config surface:** `trivy.yaml` configuration file supports all CLI flags. Environment variables (`TRIVY_SEVERITY`, `TRIVY_FORMAT`, etc.). `.trivyignore` for CVE suppression with optional expiration dates (`# exp:2025-01-01`). Rego policy bundles for misconfiguration rules. Helm chart values for Trivy Operator deployment.

## 6) Notable practices worth adopting in AGENT-33

### 1. Multi-scanner pipeline architecture
Trivy's core pattern of running independent scanner modules in parallel against a shared artifact representation is directly applicable to AGENT-33's security hardening. Instead of sequential security checks, AGENT-33 could run vulnerability scanning, secret detection, SAST, and configuration validation concurrently in a single pipeline step. Implementation path: add a `SecurityPipeline` class to `engine/src/agent33/security/` that orchestrates multiple scanner backends (Trivy for CVEs, Bandit for SAST, custom Rego for config) and merges results into a unified `SecurityReport`.

### 2. Exit-code-based policy enforcement for CI gating
Trivy's `--exit-code 1` pattern (non-zero exit when findings exceed severity threshold) is simple and universally understood by CI systems. AGENT-33 already uses this in `security-scan.yml` but should extend it to the workflow engine: workflow steps that invoke security tools should interpret exit codes as pass/fail gates. Add an `exit_code_policy` field to `WorkflowAction` that maps exit codes to workflow outcomes (continue, fail, warn).

### 3. Severity-based filtering with suppression and expiration
Trivy's `.trivyignore` with expiration dates (`# exp:2025-03-01 CVE-2024-12345`) prevents permanent risk acceptance. AGENT-33's currently empty `.trivyignore` should adopt this pattern, and the concept should extend to the governance layer: governance constraints could have expiration dates after which they reactivate, forcing periodic review.

### 4. SARIF output for unified security reporting
Trivy's SARIF (Static Analysis Results Interchange Format) output integrates with GitHub Security tab, VS Code, and other tools. AGENT-33's workflow engine should support SARIF as a standard output format for any security-related workflow action, enabling results from multiple tools (Trivy, Bandit, custom checks) to be aggregated in a single dashboard.

### 5. VEX-based contextual suppression
Rather than simply ignoring CVEs, Trivy supports VEX documents that state why a vulnerability is not applicable (e.g., "vulnerable function not called", "mitigated by network policy"). AGENT-33's governance system should adopt contextual justification for any suppressed security finding, stored as structured evidence alongside the suppression.

### 6. Database-driven vulnerability intelligence
Trivy separates the scanner engine from the vulnerability database (trivy-db), which is updated independently via GitHub releases on a schedule. AGENT-33's security scanning should decouple the scanning logic from the advisory data, allowing vulnerability databases to be updated without redeploying the application. The DB caching pattern (check age, download if stale) is already partially implemented in our CI via `actions/cache`.

## 7) Risks / limitations to account for

### 1. Database freshness lag
Trivy-db is compiled from upstream sources (NVD, GitHub Advisories, OS vendor feeds) with inherent lag. New CVEs can take 6-24 hours to appear in trivy-db after NVD publication. For AGENT-33's CI, this means a clean scan today could miss a CVE published yesterday. Mitigation: supplement Trivy scans with `osv-scanner` or GitHub Dependabot for faster advisory coverage.

### 2. False positive/negative rates in secret scanning
Trivy's secret scanner uses regex patterns which produce false positives (high-entropy strings misidentified as secrets) and miss obfuscated secrets. AGENT-33's `.trivyignore` should be prepared for secret scan noise. For AGENT-33's own secret detection (Phase 14), consider supplementing with entropy-based detection (like TruffleHog) rather than relying solely on Trivy's regex patterns.

### 3. Misconfiguration scanner scope is infrastructure-only
Trivy's config scanner checks Dockerfiles, Kubernetes manifests, Terraform, CloudFormation, Helm charts, and similar IaC files. It does not scan application-level configuration (FastAPI settings, database connection strings, JWT configuration). AGENT-33 needs application-specific configuration validation beyond what Trivy provides -- this is where custom Rego policies or dedicated SAST tools are needed.

### 4. No runtime vulnerability detection
Trivy is a static scanner -- it analyzes artifacts at rest (images, filesystems, configs). It cannot detect runtime vulnerabilities like SSRF via live endpoints, SQL injection in running APIs, or insecure deserialization at runtime. AGENT-33's security strategy must complement Trivy with runtime security tools (DAST) for Phase 14.

### 5. Large DB download on cold CI cache
The trivy-db download is ~40MB compressed (~200MB uncompressed) and the Java DB is ~250MB. On cold CI caches, this adds 15-30 seconds to scan time. AGENT-33's CI already caches the DB (lines 16-21 of `security-scan.yml`), but the `key: trivy-db-${{ github.run_id }}` pattern creates a new cache entry per run instead of reusing. Consider switching to `key: trivy-db-${{ hashFiles('engine/pyproject.toml') }}` for better cache reuse.

### 6. Limited language-specific analysis depth
Trivy detects known CVEs in dependencies (pip, npm, go.mod, etc.) but does not perform reachability analysis -- it cannot determine whether the vulnerable function is actually called in your code. This leads to noise in findings. Tools like Semgrep or CodeQL provide reachability analysis but require separate integration.

## 8) Feature extraction (for master matrix)

- **Interfaces:** CLI (primary), Server (gRPC client-server), GitHub Action, Kubernetes Operator, Go SDK library, REST API (server mode)
- **Orchestration primitives:** Scanner pipeline (analyze -> scan -> filter -> output); no agent orchestration
- **State/persistence:** Stateless per scan; vulnerability DB cached locally; server mode keeps DB in memory; Kubernetes operator stores results as Custom Resources (VulnerabilityReports, ConfigAuditReports)
- **HITL controls:** Exit-code gating, severity filtering, `.trivyignore` suppression with expiration, VEX contextual suppression, Rego policy overrides; no interactive approval flow
- **Sandboxing:** Read-only scanner (never modifies targets); signed releases with Cosign; SBOM published for Trivy itself; reproducible builds
- **Observability:** Debug logging, JSON/SARIF/template output, Prometheus metrics (server mode), `--list-all-pkgs` for full audit, GitHub Security tab integration
- **Evaluation:** Unit and integration test suite, golden-file tests against real images, community benchmark comparisons (vs. Grype, Snyk, Clair), AVD ground truth
- **Extensibility:** Plugin system (git-installable), custom Rego policies, VEX documents, Go template output, modular analyzer/scanner interfaces in Go

## 9) Evidence links

- GitHub repository: https://github.com/aquasecurity/trivy
- Official documentation: https://aquasecurity.github.io/trivy/
- Architecture overview: https://aquasecurity.github.io/trivy/latest/docs/scanner/
- Vulnerability scanning docs: https://aquasecurity.github.io/trivy/latest/docs/scanner/vulnerability/
- Misconfiguration scanning: https://aquasecurity.github.io/trivy/latest/docs/scanner/misconfiguration/
- Secret scanning: https://aquasecurity.github.io/trivy/latest/docs/scanner/secret/
- CLI reference: https://aquasecurity.github.io/trivy/latest/docs/references/configuration/cli/trivy/
- Configuration file: https://aquasecurity.github.io/trivy/latest/docs/references/configuration/config-file/
- Plugin system: https://aquasecurity.github.io/trivy/latest/docs/plugin/
- VEX support: https://aquasecurity.github.io/trivy/latest/docs/supply-chain/vex/
- GitHub Action: https://github.com/aquasecurity/trivy-action
- Trivy Operator: https://github.com/aquasecurity/trivy-operator
- Trivy vulnerability DB: https://github.com/aquasecurity/trivy-db
- Trivy checks (Rego policies): https://github.com/aquasecurity/trivy-checks
- AGENT-33 Trivy CI integration: `D:\GITHUB\AGENT33\.github\workflows\security-scan.yml` (PR #2)
