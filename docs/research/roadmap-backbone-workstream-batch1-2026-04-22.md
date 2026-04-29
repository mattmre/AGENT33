# Roadmap Backbone Workstream Batch 1 - 2026-04-22

**Purpose:** select the first bounded workstream batch for the backbone spike program so execution can begin with the minimum shared vocabulary for contracts, frozen state, and memory taxonomy.

---

## Why this batch first

From the backbone workstream decomposition, the safest first batch is:

1. **G1-W1 - Contract object inventory and boundary rules**
2. **G1-W2 - Event families, statuses, and error semantics**
3. **G2-W1 - Checkpoint unit and frozen handoff bundle**
4. **G4-W1 - Memory classes and sharing boundaries**

This batch is intentionally narrow. It avoids:

- cross-cadre proof work before object boundaries are stable
- replay example pressure before checkpoint structure is defined
- retrieval precedence work before memory classes and sharing boundaries exist

---

## Batch objective

Produce the first coherent backbone vocabulary for:

- runtime contract objects
- normalized event and error semantics
- frozen state units
- memory classes and sharing boundaries

When this batch is complete, later workstreams can operate on named objects and boundaries instead of unstable assumptions.

---

## Included workstreams

| Workstream | Why in Batch 1 | Main artifact target |
|---|---|---|
| `G1-W1` | establishes the common runtime object set | contract object inventory + schema-boundary rules |
| `G1-W2` | locks event/status/error semantics on top of G1-W1 | event taxonomy + status table + error semantics |
| `G2-W1` | defines frozen state and handoff units using the contract family | checkpoint model + handoff bundle spec |
| `G4-W1` | defines memory classes and cross-cadre sharing boundaries using contract and checkpoint concepts | memory taxonomy + sharing rules |

---

## Recommended sequencing inside the batch

1. **G1-W1**
   - finish the object inventory first

2. **G1-W2**
   - use the object inventory to separate domain, integration, and audit event families

3. **G2-W1**
   - define checkpoint and handoff units against the now-stable contract vocabulary

4. **G4-W1**
   - define memory classes and sharing rules after contract objects and frozen state units have names

Even though these are grouped as one batch, they should not be treated as fully parallel.

---

## Batch-level deliverables

This batch should yield:

1. contract object inventory
2. object boundary rules
3. normalized event family and status table
4. structured error semantics
5. checkpoint unit definition
6. frozen handoff bundle definition
7. memory taxonomy
8. cross-cadre memory sharing rules

---

## What Batch 1 intentionally does not cover

Batch 1 does **not** attempt to finish:

- Gate 1 exemplar validation flows
- Gate 2 recovery and replay examples
- Gate 4 precedence matrix
- Gate 4 provenance / why-retrieved model
- Gate 4 correction / forget / redact lifecycle

Those belong to later batches after the shared vocabulary is stable.

---

## Exit condition

Batch 1 is complete only when:

- the contract family has named object boundaries
- event/status/error semantics are normalized
- checkpoint and handoff units are defined against those contracts
- memory classes and sharing boundaries are defined against those units

Only after that should the program intensify into:

- Gate 1 exemplar validation
- Gate 2 replay / repair semantics
- Gate 4 precedence and provenance work

---

## Resulting next frontier

After Batch 1 is accepted, the next recommended batch is:

1. **G1-W3 - Cross-cadre exemplar flows and schema validation pack**
2. **G2-W2 - Recovery semantics and blocked-state vocabulary**
3. **G4-W2 - Precedence matrix and retrieval assembly rules**
4. **G4-W3 - Provenance, lineage, and why-retrieved model**

That second batch will convert the shared vocabulary from Batch 1 into proof-grade backbone semantics.
