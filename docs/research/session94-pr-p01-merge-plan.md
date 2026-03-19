# Session 94 P0.1 Merge Plan

PR scope: runtime image hardening only

## Included

- Pin `engine/Dockerfile` to a fixed Debian Trixie Python base image digest.
- Upgrade the shipped runtime image's OS packages during build so the runtime consumes current Debian security updates.
- Force the CI image build to refresh the base image during the security scan.
- Add a targeted Trivy JSON assertion that fails if `CVE-2026-0861` appears in the built runtime image.
- Record the next-wave deployment/config decisions in `docs/research/session94-p0-production-readiness-wave.md`.

## Excluded

- Kubernetes manifests
- Helm/Kustomize packaging
- secret-manager integration
- metrics, dashboards, alerts, or runbooks
- GPU / AirLLM image changes

## Local Validation

- `docker build --pull -t agent33:p01-runtime ./engine`
- `docker run --rm agent33:p01-runtime cat /etc/os-release`
- `docker run --rm agent33:p01-runtime dpkg-query -W libc6 libc-bin`
- `docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.67.2 image --severity HIGH,CRITICAL --format json --ignore-unfixed agent33:p01-runtime`
- `python scripts/verify_trivy_image.py trivy-agent33-p01-runtime.json CVE-2026-0861`
- `python - <<'PY' ... yaml.safe_load('.github/workflows/security-scan.yml') ... PY`

## Merge Gates

1. GitHub Actions `Security Scan` must pass on the branch.
2. The targeted image verification step must show no `CVE-2026-0861` hit in `results/trivy-image.json`.
3. No later slice starts before this PR is merged or explicitly paused.

## Post-Merge Queue

1. `P0.2a` deployment target decision and manifest structure
2. `P0.3a` production config / secrets model
3. `P0.2` initial Kubernetes manifests baseline
