# TurboQuant Wave 2: Security Assessment, Feasibility Analysis & Extended Literature

> **Date**: 2026-03-25  
> **Sources**: 20 parallel research agents (Wave 1 + Wave 2) + 10 targeted web searches  
> **Companion**: See `turboquant-research.md` for core algorithm details and AGENT-33 integration roadmap

---

## Executive Summary

This document synthesizes Wave 2 research covering three concerns raised after the initial TurboQuant investigation:

1. **Security Assessment**: All recommended libraries (FAISS, bitsandbytes, QJL, KIVI) pass supply-chain security review. **No honeypot indicators found.** The biggest actual security risks in AGENT-33 are pre-existing (Ollama CVEs, unpinned llama.cpp downloads, pickle deserialization via AirLLM) — not from the proposed quantization libraries.

2. **Qwen/3090 Feasibility**: You do **NOT** need to train a model. TurboQuant is data-oblivious (algorithmic, no training). A 3090 can run Qwen2.5-14B at Q4_K_M comfortably, train FAISS indexes in minutes, and QLoRA fine-tune up to 14B models. The 3090 is fully sufficient for every phase of the proposed integration.

3. **Extended Literature**: 45+ papers cataloged across Google, OpenAI, Meta, Microsoft, Alibaba/DAMO, DeepSeek, and top venues (ICLR, NeurIPS, ICML, AAAI, MLSys). The rotation-based quantization paradigm (TurboQuant → QuaRot → SpinQuant) is the dominant research direction.

---

## Part 1: Security Assessment

### 1.1 Proposed Library Risk Matrix

| Library | Maintainer | CVEs Known | PyPI Status | Typosquat Risk | Supply Chain | **Verdict** |
|---------|-----------|------------|-------------|---------------|-------------|-------------|
| **FAISS** (`faiss-cpu` v1.13.2) | Meta AI (verified org) | ✅ None (Snyk, Safety DB, Sonatype confirm) | Semi-official (conda preferred) | ⚠️ Medium — bare `faiss` ≠ official | ✅ None known | **LOW ✅** |
| **bitsandbytes** | Tim Dettmers / bitsandbytes-foundation | ✅ None | ✅ Official | ✅ Low | ✅ None known | **LOW ✅** |
| **QJL** | Amir Zandieh (Google DeepMind, AAAI pub) | ✅ None | N/A (not on PyPI) | N/A | ✅ None known | **LOW ✅** |
| **KIVI** | Jingyang Yuan (academic, peer-reviewed) | ✅ None | N/A (not on PyPI) | N/A | ✅ None known | **LOW ✅** |

### 1.2 Is TurboQuant a Honeypot?

**No.** Multiple independent signals confirm legitimacy:

- **Academic provenance**: Published at ICLR 2026 (top-1 ML venue, rigorous peer review)
- **Author verification**: Amir Zandieh — long publication history at Google DeepMind, EPFL, Inria (DBLP-verifiable)
- **Google Research blog**: Official announcement at research.google/blog (not a third-party claim)
- **Data-oblivious design**: Actually a security *advantage* — no dataset-specific information leakage
- **No suspicious patterns**: Algorithm is mathematically grounded in well-understood theory (Johnson-Lindenstrauss lemma, polar decomposition, Lloyd-Max quantization)
- **Multiple independent coverage**: MarkTechPost, Help Net Security, Pulse24, ArXiv, all independently verified

**Third-party implementations**: `tonbistudio/turboquant-pytorch` exists on GitHub — no formal security audit, treat as experimental reference code only. Inherits PyTorch security context (CVE-2025-32434 in PyTorch ≤2.5.1 allows RCE via `torch.load()` — patched in 2.6.0).

### 1.3 Pre-Existing Security Risks in AGENT-33 (Higher Priority)

The security audit revealed that AGENT-33's **current** stack has more pressing security concerns than the proposed quantization libraries:

| # | Risk | Severity | Location | Fix |
|---|------|----------|----------|-----|
| 1 | **Ollama RCE history** (CVE-2024-37032, CVSS 9.1) | 🔴 CRITICAL | `config.py:26` | Pin version ≥0.1.34, restrict network |
| 2 | **Unpinned llama.cpp downloads** | 🔴 CRITICAL | `download_heretic.ps1:7` | Pin release tag + SHA-256 verify |
| 3 | **No model hash verification** | 🔴 HIGH | `download_model.py:26-29` | Use `snapshot_download(revision="commit_hash")` |
| 4 | **Pickle deserialization via AirLLM** | ⚠️ MEDIUM | `airllm_provider.py:106` | Enforce safetensors-only loading |
| 5 | **GGUF parser bugs** (CVE-2024-42479) | ⚠️ MEDIUM | llama.cpp transitive | Pin llama.cpp version |
| 6 | **Ollama DNS rebinding** | ⚠️ MEDIUM | Docker compose | Ensure port 11434 not published to host |

**Recommendation**: Address items 1-3 before adding any new dependencies.

### 1.4 FAISS-Specific Security Guidance

```
✅ APPROVED for integration with conditions:
```

1. Install via `pip install faiss-cpu==1.13.2` with hash pinning (or conda-forge)
2. **Never** call `faiss.read_index()` on files from untrusted sources (binary deserialization risk)
3. The bare `faiss` package on PyPI is NOT the official one — always use `faiss-cpu` or `faiss-gpu`
4. Add to Trivy/Dependabot scanning
5. Place in optional dependency group: `[project.optional-dependencies.quantized]`

### 1.5 Quantization-Specific Attack Vectors

| Attack Type | Real Risk? | Relevance to AGENT-33 |
|-------------|-----------|----------------------|
| Quantized model trojans (backdoors surviving quantization) | ✅ Real (research-demonstrated) | LOW — AGENT-33 doesn't quantize models, uses pre-quantized GGUF from trusted sources |
| Pickle bomb / RCE via model files | ✅ Real (documented attacks on HuggingFace Hub) | MEDIUM — AirLLM path could load pickle-format models |
| FAISS index poisoning | ⚠️ Theoretical | LOW — AGENT-33 controls its own embedding pipeline |
| PyPI typosquatting of ML packages | ✅ Real (hundreds removed yearly) | LOW — use exact package names with hash verification |

---

## Part 2: Qwen Model & RTX 3090 Feasibility

### 2.1 Critical Clarification: Qwen Cannot "Perform" Quantization

**Quantization is a numerical algorithm, not an LLM task.** Qwen is a language model — it processes text tokens, not weight tensors. It cannot take a model as input and output quantized weights.

| Use Case | Feasible? | Explanation |
|----------|-----------|-------------|
| Qwen performs quantization directly | ❌ **No** | LLMs don't quantize — tools like AutoGPTQ/AWQ/FAISS do |
| Qwen helps *write* quantization code | ✅ **Yes** | Qwen2.5-Coder-14B-Q4 is excellent for code generation |
| Qwen is *subject of* quantization | ✅ **Yes** | Pre-quantized Qwen models are widely available |
| Train a custom quantization model | ❌ **Not needed** | TurboQuant is data-oblivious — no training required |

### 2.2 What Fits on a 3090 (24GB VRAM)

#### Inference

| Model | Quantization | VRAM | Fits? | Context |
|-------|-------------|------|-------|---------|
| Qwen2.5-7B | FP16 | ~14.5 GB | ✅ Yes | ~16K |
| **Qwen2.5-14B** | **Q4_K_M (GGUF)** | **~8.5 GB** | **✅ Sweet spot** | **~16-24K** |
| Qwen2.5-32B | Q4_K_M | ~18-19 GB | ⚠️ Tight | ~4-8K |
| Qwen2.5-72B | Any | >36 GB | ❌ No | Use AirLLM |
| Qwen3-14B | Q4 | ~8-9 GB | ✅ Yes | Good for agents |

#### Training / Fine-tuning (QLoRA)

| Model | Method | VRAM | Fits? |
|-------|--------|------|-------|
| Qwen2.5-7B | QLoRA r=64 | ~14-18 GB | ✅ Yes |
| Qwen2.5-14B | QLoRA r=16, batch=1 | ~16-20 GB | ✅ Tight |
| Qwen2.5-32B | QLoRA | ~40+ GB | ❌ No |

#### Embedding Model Training

| Model | Params | Training VRAM | Fits? |
|-------|--------|---------------|-------|
| nomic-embed-text | 137M | ~2-4 GB | ✅ Trivially |
| bge-large-en-v1.5 | 335M | ~4-6 GB | ✅ Easily |
| Jina-embeddings-v3 | 572M | ~6-10 GB | ✅ Yes |

**The 3090 is excellent for embedding model training** — these models are 100-500M params and fit with huge batch sizes.

### 2.3 TurboQuant on 3090 — What's Actually Needed

| Operation | Training Needed? | GPU Needed? | 3090 Can Do It? |
|-----------|-----------------|-------------|-----------------|
| TurboQuant rotation + SQ | ❌ Data-oblivious | CPU is fine | ✅ N/A |
| FAISS OPQ rotation matrix | Light (~minutes) | ✅ Optional | ✅ Yes, fast |
| FAISS PQ codebooks | Light (~minutes) | ✅ Optional | ✅ Yes |
| GPTQ calibrate 7B model | Calibration (~1hr) | ✅ Yes | ✅ Yes |
| Fine-tune nomic-embed-text | Real training (~1hr) | ✅ Yes | ✅ Trivial |

### 2.4 RTX 3090 Hardware Limitations

| Feature | 3090 (Ampere) | H100 (Hopper) | Impact |
|---------|--------------|---------------|--------|
| FP8 | ❌ No | ✅ Yes | Can't use vLLM FP8 KV cache → use INT8/Q8_0 instead |
| VRAM | 24 GB | 80 GB | Max ~32B Q4, no 72B |
| Bandwidth | 936 GB/s | 3,350 GB/s | ~3.5× slower memory-bound ops |
| INT8 TOPS | 284 | 1,980 | Plenty for quantized inference |

**Bottom line**: The 3090 can do everything AGENT-33 needs. Use `OLLAMA_KV_CACHE_TYPE=q8_0` (not FP8).

---

## Part 3: Extended Literature Survey

### 3.1 Paper Catalog — 45 Papers by Organization

#### Tier 1: Core TurboQuant Family (Google Research)

| # | Paper | Venue | arXiv | Key Contribution |
|---|-------|-------|-------|-----------------|
| 1 | **TurboQuant** | ICLR 2026 | 2504.19874 | Two-stage data-oblivious VQ: PolarQuant + QJL |
| 2 | **PolarQuant** | AISTATS 2026 | 2502.02617 | Polar decomposition + random rotation → zero-overhead direction quant |
| 3 | **QJL** | AAAI 2025 | 2406.03462 | 1-bit JL transform for KV cache, unbiased estimator |

#### Tier 2: Rotation-Based Quantization (THE Dominant Paradigm)

| # | Paper | Authors/Org | Venue | arXiv | Key Insight | Relevance |
|---|-------|------------|-------|-------|-------------|-----------|
| 4 | **QuaRot** | ETH/IST Austria | NeurIPS 2024 | 2404.00456 | Random Hadamard rotation removes outliers → 4-bit end-to-end | **HIGH** — same rotation trick as TurboQuant |
| 5 | **SpinQuant** | Meta FAIR | ICLR 2025 | 2405.16406 | *Learned* rotation matrices outperform random by up to 45.1% | **HIGH** — TurboQuant enhancement path |
| 6 | **QuIP#** | Cornell | ICML 2024 | 2307.13304 | Hadamard incoherence + E8 lattice codebook for 2-bit weights | **HIGH** — shares rotation preprocessing |
| 7 | **FlatQuant** | Various | arXiv 2024 | 2410.09426 | Flatness-aware rotation matrices | MEDIUM |

**Key insight**: Papers 1-7 form a coherent research thread — **rotation preprocessing before quantization** is the single most important algorithmic pattern in 2024-2026 quantization research.

#### Tier 3: KV Cache Quantization

| # | Paper | Venue | arXiv | Key Contribution |
|---|-------|-------|-------|-----------------|
| 8 | **KIVI** | ICML 2024 workshop | 2402.02750 | Tuning-free 2-bit asymmetric KV quant |
| 9 | **KVQuant** | MLSys 2025 | 2401.18079 | Non-uniform quant for 10M context length |
| 10 | **GEAR** | arXiv 2024 | 2403.05527 | Low-rank + sparse + uniform KV compression |
| 11 | **CacheGen** | SIGCOMM 2024 | — | KV cache streaming/codec for distributed inference |
| 12 | **QServe** | MLSys 2025 | — | W4A8KV4 system co-design for serving throughput |

#### Tier 4: Weight Quantization (Post-Training)

| # | Paper | Authors/Org | Venue | arXiv | Key Contribution |
|---|-------|------------|-------|-------|-----------------|
| 13 | **GPTQ** | IST Austria | ICLR 2023 | 2210.17323 | Hessian-based one-shot PTQ (gold standard) |
| 14 | **AWQ** | MIT Han Lab | MLSys 2024 | 2306.00978 | Activation-aware per-channel weight scaling |
| 15 | **SmoothQuant** | MIT/Tsinghua | ICML 2023 | 2211.10438 | Activation→weight difficulty migration for W8A8 |
| 16 | **SqueezeLLM** | UC Berkeley | ICML 2024 | 2306.07629 | Dense-and-sparse decomposition for 3-bit |
| 17 | **AQLM** | Yandex/IST | ICML 2024 | 2401.06118 | Multi-codebook additive VQ for <2-bit |
| 18 | **OmniQuant** | Shanghai AI Lab | ICLR 2024 | 2308.13137 | Learnable weight clipping + equivalent transform |
| 19 | **Atom** | Various | MLSys 2024 | 2310.19102 | Mixed-precision with dynamic activation reordering |
| 20 | **OneBit** | Various | arXiv 2024 | 2402.11295 | 1-bit via sign decomposition + low-rank value matrices |
| 21 | **BiLLM** | Various | ICML 2024 | 2402.04291 | Binary weights via Hessian salient weight ID |

#### Tier 5: 1-bit / Ternary Models (Microsoft BitNet Family)

| # | Paper | Venue | arXiv | Key Contribution |
|---|-------|-------|-------|-----------------|
| 22 | **BitNet** | arXiv 2023 | 2310.11453 | 1-bit weight transformers (BitLinear layers) |
| 23 | **BitNet b1.58** | arXiv 2024 | 2402.17764 | Ternary {-1,0,+1} weights matching FP16 at 3B+ |
| 24 | **BitNet a4.8** | arXiv 2024 | 2411.04965 | 4-bit activations for 1-bit LLMs |
| 25 | **BitNet b1.58-2B-4T** | arXiv 2025 | 2504.12285 | First open-source 2B ternary model (MIT license) |
| 26 | **BitDistill** | MarkTechPost 2025 | — | Distill FP16→1.58-bit, 10× memory savings |

**Production note**: BitNet is now production-viable (bitnet.cpp, MIT license). Runs 100B models on CPU at 5-7 tok/s. x86-64 only for optimized inference. Interesting AGENT-33 integration candidate for CPU-only deployments.

#### Tier 6: Efficient Attention & Inference

| # | Paper | Venue | arXiv | Key Contribution |
|---|-------|-------|-------|-----------------|
| 27 | **FlashAttention** | NeurIPS 2022 | 2205.14135 | IO-aware tiled attention (prerequisite for KV quant) |
| 28 | **FlashAttention-2** | ICLR 2024 | 2307.08691 | 2× speedup via better work partitioning |
| 29 | **FlashAttention-3** | NeurIPS 2024 | 2407.08691 | H100 pipelining, FP8 KV support |
| 30 | **Medusa** | ICML 2024 | 2401.10774 | Multi-head speculative decoding |

#### Tier 7: Embedding Compression & Vector Search

| # | Paper | Venue | arXiv | Key Contribution |
|---|-------|-------|-------|-----------------|
| 31 | **Matryoshka (MRL)** | NeurIPS 2022 | 2205.13147 | Multi-resolution embeddings (truncate dims) |
| 32 | **SMEC** | EMNLP 2025 | 2510.12474 | Sequential MRL + adaptive dimension selection (14× lossless compression) |
| 33 | **Product Quantization** | IEEE TPAMI 2011 | classic | Foundation for FAISS PQ and all modern VQ systems |
| 34 | **FAISS** | IEEE TBD 2021 | 1702.08734 | Gold standard vector search (32K stars) |
| 35 | **RaBitQ** | SIGMOD 2024 | 2405.12497 | Random rotation + 1-bit ANN with error bounds |

#### Tier 8: Industry-Scale Quantization

| # | Paper | Authors/Org | Venue | arXiv | Key Contribution |
|---|-------|------------|-------|-------|-----------------|
| 36 | **DeepSeek V3** | DeepSeek AI | arXiv 2024 | 2412.19437 | First 671B MoE trained entirely in FP8; block-wise FP8 quant |
| 37 | **Qwen3 Quantization Study** | Alibaba DAMO + universities | arXiv 2025 | 2505.02214 | Systematic evaluation of Qwen3 under 1-8 bit PTQ |
| 38 | **On-Device Qwen2.5** | Various | arXiv 2025 | 2504.17376 | AWQ + FPGA acceleration, 55% compression on edge |
| 39 | **LLM.int8()** | UW/Meta (Dettmers) | NeurIPS 2022 | 2208.07339 | Mixed-precision INT8 with outlier decomposition |
| 40 | **QLoRA** | Dettmers et al. | NeurIPS 2023 | 2305.14314 | 4-bit NF4 base + LoRA fine-tuning (65B on single GPU) |

#### Tier 9: Microsoft/Intel/Other

| # | Paper | Venue | arXiv | Key Contribution |
|---|-------|-------|-------|-----------------|
| 41 | **ZeroQuant** | NeurIPS 2022 | 2206.01861 | Group-wise weight + token-wise activation quant |
| 42 | **ZeroQuant-V2** | arXiv 2023 | 2303.08302 | Low-rank error compensation for PTQ |
| 43 | **FP8 PTQ** | MLSys 2024 | (proceedings) | Systematic FP8 evaluation across architectures |
| 44 | **Quantization Hurts Reasoning?** | OpenReview 2025 | — | W8A8 lossless; W4A16 borderline; lower destroys reasoning |
| 45 | **Comprehensive Eval of LLM Quant** | arXiv 2025 | 2507.17417 | Tongji/Bristol decoupled eval: rotation + error mitigation |

### 3.2 Research Landscape Summary

| Organization | Papers | Key Direction | AGENT-33 Relevance |
|-------------|--------|--------------|-------------------|
| **Google Research** | 3 core + TurboQuant blog | Data-oblivious rotation + 1-bit correction | **Highest** — core algorithm |
| **Meta FAIR** | SpinQuant, FAISS, Flash Attention, SqueezeLLM | Learned rotations, production vector search | **High** — FAISS is our production path |
| **Microsoft** | BitNet family (6 papers) | 1-bit/ternary models, CPU inference | **Medium** — interesting for CPU-only mode |
| **MIT Han Lab** | AWQ, SmoothQuant | Production-grade W4/W8 quantization | **Medium** — Ollama handles this |
| **Alibaba/DAMO** | Qwen3 quant study, on-device Qwen | Qwen-specific PTQ evaluation | **High** — AGENT-33 uses Qwen |
| **DeepSeek** | V3 FP8 training | FP8 mixed-precision training at scale | **Low** — training-time, not inference |
| **ETH Zurich/IST** | QuaRot, GPTQ, AQLM | Rotation + Hessian-based PTQ | **High** — theoretical foundations |
| **UC Berkeley** | KVQuant, SqueezeLLM | Non-uniform quant, dense-sparse decomp | **Medium** — KV cache alternatives |

### 3.3 The Dominant Research Pattern: Rotation-Based Quantization

The single most important finding across 45 papers is that **7 independent groups converged on the same technique**: apply a rotation transformation before quantization to eliminate outliers and distribute information evenly across coordinates.

```
TurboQuant (Google)    → Random Hadamard rotation
QuaRot (ETH Zurich)    → Random Hadamard rotation
SpinQuant (Meta FAIR)  → LEARNED rotation matrices (best results)
QuIP# (Cornell)        → Hadamard incoherence processing
PolarQuant (Google)    → Random rotation + polar decomposition
FlatQuant (Various)    → Flatness-aware rotation
RaBitQ (SIGMOD)        → Random rotation + 1-bit for ANN
```

This convergence validates TurboQuant's approach and suggests that AGENT-33's `RotationPreprocessor` module should support both random Hadamard and potentially learned rotations (SpinQuant-style).

---

## Part 4: Production Landscape — What's Battle-Tested

### 4.1 Battle-Tested (Safe for Production)

| Technique | Where Deployed | Stars/Users |
|-----------|---------------|-------------|
| **GGUF Q4_K_M** | llama.cpp, Ollama | 70K + 100K+ stars |
| **GPTQ INT4** | vLLM, HuggingFace, TRT-LLM | 4K stars, millions of users |
| **AWQ INT4** | vLLM, TRT-LLM, production | 3.5K stars |
| **FP8 (H100)** | OpenAI, Google, Anthropic, all providers | Hardware-native |
| **Q8_0 KV cache** | llama.cpp, Ollama | Widely used |
| **FAISS OPQ+SQ** | Meta production (billions of vectors) | 32K stars |
| **Pinecone BQ/PQ** | Pinecone cloud | Production GA |
| **Weaviate PQ/BQ/SQ** | Weaviate cloud | Production GA |
| **pgvector halfvec** | PostgreSQL | Production GA since v0.7.0 |
| **bitsandbytes NF4** | HuggingFace ecosystem | 6.5K stars |

### 4.2 Research-Only (Not Production-Ready)

| Technique | Status | Gap |
|-----------|--------|-----|
| **TurboQuant** | Paper only, no official impl | Engineering needed |
| **PolarQuant** | Paper only | Same |
| **QJL** | Research code, CUDA kernels exist | Not in any engine |
| **BitNet** | MIT-licensed, bitnet.cpp works | x86-only, limited model selection |
| **KIVI 2-bit KV** | Research code | Not in vLLM/TRT-LLM |
| **1-bit weight models** | Research | Requires training from scratch |

### 4.3 Production Vector DB Quantization Support

| Database | SQ (INT8) | PQ | BQ (1-bit) | halfvec (FP16) | HNSW |
|----------|----------|-----|-----------|---------------|------|
| **Pinecone** | ✅ | ✅ | ✅ | — | ✅ |
| **Weaviate** | ✅ (v1.26+) | ✅ | ✅ (v1.23+) | — | ✅ |
| **Milvus** | ✅ SQ8 | ✅ IVF_PQ | ✅ BIN_FLAT | — | ✅ |
| **pgvector** | ❌ | ❌ | ✅ bit type | ✅ (v0.7.0+) | ✅ |
| **ChromaDB** | ❌ | ❌ | ❌ | ❌ | ✅ (hnswlib) |
| **FAISS** | ✅ 4/8-bit | ✅ OPQ | — | — | ✅ (CPU only) |

**AGENT-33 uses pgvector** → immediate wins: HNSW index + halfvec. For deeper compression: FAISS sidecar.

---

## Part 5: Recommendations & Next Steps

### 5.1 Security Actions (Priority Order)

1. **[P0]** Pin Ollama version ≥0.1.34, ensure port 11434 not published to host
2. **[P0]** Pin llama.cpp release tag + SHA-256 verification in `download_heretic.ps1`
3. **[P1]** Add model hash verification to `download_model.py`
4. **[P1]** Enforce safetensors-only loading in AirLLM path
5. **[P2]** Add FAISS to optional dependency group with version pin + hash

### 5.2 Zero-Code Quick Wins

1. `OLLAMA_KV_CACHE_TYPE=q8_0` — 50% KV cache memory savings
2. `OLLAMA_FLASH_ATTENTION=1` — required for KV quant + faster attention
3. pgvector HNSW index (single SQL migration) — better recall than IVFFlat
4. Fix `Vector(1536)` → `Vector(768)` dimension mismatch

### 5.3 Qwen/3090 Practical Path

```
Path A: Use Qwen as coding assistant for quantization development
  → Run Qwen2.5-Coder-14B-Q4 via Ollama (~9GB)
  → Use to write TurboQuantCompressor, FAISS integration code
  → Remaining ~15GB for testing

Path B: Production agent tasks + quantized embeddings  
  → Run Qwen2.5-14B-Q4 via Ollama (~9GB)
  → Enable OLLAMA_KV_CACHE_TYPE=q8_0
  → Run nomic-embed-text alongside (~1GB)
  → Implement embedding compression (Phase 2)
  → Total: ~11GB, leaving 13GB headroom
```

### 5.4 Top 10 Papers for Deep Review

Based on relevance to AGENT-33 integration, these are the highest-value papers to read:

| Rank | Paper | Why |
|------|-------|-----|
| 1 | **TurboQuant** (2504.19874) | Core algorithm, direct integration target |
| 2 | **SpinQuant** (2405.16406) | Learned rotations > random — future enhancement |
| 3 | **QuaRot** (2404.00456) | Same rotation paradigm, practical end-to-end 4-bit |
| 4 | **SMEC/Matryoshka** (2510.12474 / 2205.13147) | 14× embedding compression, Jina v3 already supports MRL |
| 5 | **FAISS** (1702.08734) | Production implementation target, OPQ = TurboQuant Stage 1 |
| 6 | **QJL** (2406.03462) | Stage 2 of TurboQuant, 1-bit error correction |
| 7 | **Qwen3 Quantization** (2505.02214) | Direct benchmarks for AGENT-33's primary model family |
| 8 | **FlashAttention-3** (2407.08691) | H100 FP8 KV kernels, attention optimization |
| 9 | **RaBitQ** (2405.12497) | Random rotation + 1-bit for ANN — direct competitor |
| 10 | **DeepSeek V3** (2412.19437) | FP8 training at scale, block-wise quantization design |

---

## Appendix A: Source URLs & Citations

### Papers (arXiv)
- TurboQuant: https://arxiv.org/abs/2504.19874
- PolarQuant: https://arxiv.org/abs/2502.02617
- QJL: https://arxiv.org/abs/2406.03462
- SpinQuant: https://arxiv.org/abs/2405.16406
- QuaRot: https://arxiv.org/abs/2404.00456 / https://spcl.inf.ethz.ch/Publications/index.php?pub=526
- RaBitQ: https://arxiv.org/abs/2405.12497
- SMEC: https://arxiv.org/abs/2510.12474
- MRL: https://arxiv.org/abs/2205.13147
- BitNet b1.58-2B-4T: https://arxiv.org/abs/2504.12285
- DeepSeek V3: https://arxiv.org/abs/2412.19437
- Qwen3 Quantization: https://arxiv.org/abs/2505.02214
- Comprehensive Eval 2025: https://arxiv.org/abs/2507.17417

### GitHub Repositories
- FAISS: https://github.com/facebookresearch/faiss (32K stars)
- SpinQuant: https://github.com/facebookresearch/SpinQuant
- QJL: https://github.com/amirzandieh/QJL
- BitNet: https://github.com/microsoft/BitNet
- Awesome Quantization Papers: https://github.com/Zhen-Dong/Awesome-Quantization-Papers
- turboquant-pytorch (3rd-party): https://github.com/tonbistudio/turboquant-pytorch

### Security References
- FAISS Snyk: https://security.snyk.io/package/pip/faiss-cpu
- FAISS Safety DB: https://data.safetycli.com/packages/pypi/faiss-cpu/
- PyTorch CVE-2025-32434: https://gbhackers.com/critical-pytorch-vulnerability/
- BitNet deployment guide: https://esso.dev/blog-posts/deploying-microsoft-bit-net-1-58-bit-llm-a-complete-guide-with-all-the-gotchas

### Industry Coverage
- Google Research Blog: https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/
- MarkTechPost: https://www.marktechpost.com/2026/03/25/google-introduces-turboquant/
- Help Net Security: https://www.helpnetsecurity.com/2026/03/25/google-turboquant-ai-model-compression/
- SmoothQuant project page: https://hanlab.mit.edu/projects/smoothquant
