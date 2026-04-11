# Session 124 POST-3.2 Scope Lock - Pack Registry v1

## Goal

Complete the next pack-ecosystem slice by adding revocation support to the GitHub JSON registry flow and by extending pack provenance verification to understand Sigstore metadata without breaking the existing HMAC path.

## Included work

- Extend `agent33.packs.hub` with:
  - per-entry revocation fields
  - registry-level revocation list parsing
  - revocation status lookup
  - revoked-pack rejection before download
- Extend provenance models and verification with:
  - `SigstoreBundle` metadata
  - `algorithm="sigstore"` dispatch
  - graceful failure when Sigstore runtime support is unavailable
- Expose revocation status through:
  - `GET /v1/packs/hub/revocation/{name}`
  - `agent33 packs revocation-status`
- Add focused regression coverage for hub revocation, route behavior, CLI behavior, and Sigstore verification dispatch.

## Explicit non-goals

- redesigning broader remote pack transport or archive format
- replacing the existing HMAC signing path
- introducing a hosted registry service beyond the GitHub JSON index
- implementing pack publishing automation beyond the current validate-and-template flow

## Delivered in PR #395

- revocation metadata and registry-level revocation records in `agent33.packs.hub`
- revoked-download rejection before any network activity
- Sigstore-aware provenance verification dispatch with graceful degradation when runtime support is absent
- revocation status route and CLI surface
- focused POST-3.2 regression coverage
