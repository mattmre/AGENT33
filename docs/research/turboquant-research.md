# TurboQuant Research: Extreme AI Compression for AGENT-33

> **Date**: 2026-03-25  
> **Sources**: 10 parallel research agents across papers, implementations, and codebase analysis  
> **Papers**: TurboQuant (arXiv:2504.19874, ICLR 2026), PolarQuant (arXiv:2502.02617, AISTATS 2026), QJL (AAAI 2025)

---

## Executive Summary

Google's **TurboQuant** is a two-stage, data-oblivious vector quantization algorithm that achieves **6× KV cache memory reduction** and **8× attention speedup** on H100 GPUs with **zero accuracy loss** and **no calibration data required**. It combines PolarQuant (polar coordinate decomposition with random rotation) and QJL (1-bit Johnson-Lindenstrauss error correction) to reach near-optimal distortion at 2.5–3.5 bits per coordinate.

For AGENT-33, this research identifies **two concrete integration surfaces**:

1. **Embedding vector compression** — 8–16× storage reduction in pgvector/LRU cache via TurboQuant-style scalar quantization with rotation preprocessing
2. **LLM inference acceleration** — KV cache quantization via Ollama/vLLM server configuration (infrastructure-level, no code changes)

---

## 1. The TurboQuant Algorithm Family

### 1.1 TurboQuant — Two-Stage Pipeline

```
Input vector x ∈ ℝᵈ
    │
    ▼
┌─────────────────────┐
│ Random Rotation      │  y = R · x   (Randomized Hadamard Transform)
│ (deterministic seed) │  R is O(d log d) to apply, 0 bytes to store
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ STAGE 1: PolarQuant │  Decompose y → (‖y‖, ŷ)  where ŷ = y/‖y‖
│                     │  Quantize norm ‖y‖ → scalar quantizer (8-16 bits)
│                     │  Quantize direction ŷ → per-coord scalar quantizer (b bits × d)
│                     │  Reconstruct: Q₁(y) = q(‖y‖) · q(ŷ)
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ STAGE 2: QJL        │  Residual: r = y − Q₁(y)
│ (1-bit correction)  │  Store: bᵢ = sign(⟨r, gᵢ⟩) for i=1..m
│                     │  (gᵢ are shared random Gaussians from seed)
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ Reconstruction      │  x̂ = Rᵀ · (Q₁(y) + α/m · Gᵀ · b)
└─────────────────────┘
```

**Key properties:**
- **Data-oblivious**: No calibration dataset needed — rotation makes all distributions quantizer-friendly
- **Near-optimal**: Achieves ≈2.7× the information-theoretic rate-distortion lower bound
- **Zero overhead**: No per-group scale factors stored (PolarQuant eliminates them via normalization absorption)
- **Unbiased**: QJL stage provides mathematically unbiased error correction

### 1.2 PolarQuant — Zero-Overhead Direction Quantization

**Core insight**: Convert vectors from Cartesian to polar coordinates before quantizing.

| Step | Operation | Why It Works |
|------|-----------|-------------|
| 1. Random rotation | y = RHT(x) using randomized Hadamard | Spreads outliers across all dimensions; makes distribution isotropic |
| 2. Polar decomposition | r = ‖y‖₂, ŷ = y/r | Separates magnitude (1 scalar) from direction (unit sphere) |
| 3. Direction quantization | Per-coordinate uniform SQ on ŷ | After rotation, coordinates are ≈ i.i.d. in [-1/√d, 1/√d] — fixed range, no scale factors needed |
| 4. Norm absorption | Skip storing r | LayerNorm/RMSNorm in subsequent transformer layer absorbs the missing magnitude |

**Memory comparison (4-bit, group size 128):**

| Method | Nominal bits | Scale overhead | Effective bits |
|--------|-------------|----------------|----------------|
| GPTQ (g=128) | 4.00 | +0.125 | **4.125** |
| AWQ (g=128) | 4.00 | +0.125 | **4.125** |
| QuIP# | 4.00 | +0.125 | **4.125** |
| **PolarQuant** | 4.00 | **+0.000** | **4.000** |

### 1.3 QJL — 1-Bit Error Correction with Zero Overhead

**Asymmetric precision trick**: Keep full-precision queries × 1-bit cached keys.

```
Estimator:  ⟨q, k⟩ ≈ (‖k‖/m) · Σᵢ (rᵢᵀq) · sign(rᵢᵀk)
```

| Component | Memory | Notes |
|-----------|--------|-------|
| Sign bits sign(Rk) | m bits per key | The compressed representation |
| Key norms ‖k‖ | 1 float16 per key | 2 bytes |
| Random matrix R | **0 bytes** | Generated on-the-fly from PRNG seed |
| Scales/zero-points | **0 bytes** | Not needed |

**Compression**: At m=d, achieves ~16× compression of KV cache.

---

## 2. Experimental Results (From Paper)

### 2.1 KV Cache Compression

| Model | Method | Bits | Benchmark Score | Memory Reduction |
|-------|--------|------|----------------|-----------------|
| Gemma/Mistral | FP16 baseline | 16 | 100% | 1× |
| Gemma/Mistral | KIVI | 2-4 | ~95% | ~4× |
| Gemma/Mistral | PolarQuant | 3 | ~99% | ~5× |
| Gemma/Mistral | **TurboQuant** | **3** | **~100%** | **6×** |

### 2.2 GPU Speedup (H100)

| Sequence Length | Speedup vs FP16 |
|----------------|----------------|
| 2K | ~2× |
| 8K | ~4-5× |
| 32K | ~6-7× |
| 128K+ | **~8×** |

### 2.3 Vector Search (1@k Recall)

TurboQuant consistently outperforms Product Quantization (PQ) and RabbiQ baselines in high-dimensional vector search recall, despite those baselines using dataset-specific tuning.

---

## 3. Competitive Landscape

### 3.1 KV Cache Quantization Methods

| Method | Repo | Stars | Bits | Calibration? | Theory Guarantee? |
|--------|------|-------|------|-------------|-------------------|
| **KIVI** | `jy-yuan/KIVI` | ~300 | 2 | No (tuning-free) | No |
| **KVQuant** | `SqueezeAILab/KVQuant` | ~300 | 2-4 | Yes (NUQ) | No |
| **GEAR** | `HaoKang-Timmy/Gear` | ~100 | 2-4 | Yes | No |
| **QJL** | `amirzandieh/QJL` | ~50 | 1 | No | **Yes (JL bound)** |
| **TurboQuant** | *No public impl* | — | 2.5-3.5 | **No** | **Yes (2.7× optimal)** |

### 3.2 Weight Quantization Methods

| Method | Repo | Stars | Approach |
|--------|------|-------|----------|
| **GPTQ** | `IST-DASLab/gptq` | ~4K | Hessian-based post-training |
| **AWQ** | `mit-han-lab/llm-awq` | ~3.5K | Activation-aware scaling |
| **QuIP#** | `cornell-relaxml/quip-sharp` | ~800 | Hadamard + lattice VQ |
| **AQLM** | `Vahe1994/AQLM` | ~1K | Additive multi-codebook VQ |
| **bitsandbytes** | `bitsandbytes-foundation/bitsandbytes` | ~6.5K | NF4/FP4/INT8 |

### 3.3 Production Inference Engines (with KV Cache Support)

| Engine | Stars | KV Cache Quant | Integration |
|--------|-------|---------------|-------------|
| **llama.cpp** | ~70K | Q4_0/Q8_0 KV types | GGUF format |
| **vLLM** | ~35K | FP8 KV cache | `--kv-cache-dtype fp8_e5m2` |
| **TensorRT-LLM** | ~9K | INT8/FP8 KV cache | NVIDIA Hopper optimized |
| **Ollama** | ~100K+ | q4_0/q8_0 KV cache | `OLLAMA_KV_CACHE_TYPE=q8_0` |
| **Flash Attention** | ~15K | FP8 KV support | Kernel-level |

### 3.4 Vector Search / Embedding Compression

| Library | Stars | Quantization | Best For |
|---------|-------|-------------|----------|
| **FAISS** | ~32K | PQ, OPQ, SQ (4/8-bit) | Gold standard VQ |
| **ScaNN** | (Google) | Anisotropic PQ | Best recall |
| **pgvector** | ~13K | halfvec, binary (0.7+) | PostgreSQL native |
| **USearch** | ~2K | f16, i8, binary | Lightweight |

---

## 4. AGENT-33 Integration Analysis

### 4.1 Current Architecture (Embedding Path)

```
User Query
  → EmbeddingProvider.embed(text)        # Ollama nomic-embed-text → list[float]
  → EmbeddingCache (LRU, SHA-256, 1024)  # Stores full float32 vectors
  → LongTermMemory.store(text, emb)      # INSERT INTO memory_records (pgvector)
  → LongTermMemory.search(emb, top_k)    # SELECT ... ORDER BY embedding <=> query
  → HybridSearcher.search(query)         # RRF fusion: pgvector + BM25
  → RAGPipeline.query(text)              # Augmented prompt assembly
```

**Current state**: Zero compression. Full float32/64 everywhere. `Vector(1536)` hardcoded in schema. IVFFlat index with 100 lists. No HNSW.

### 4.2 Critical Findings

| Finding | Impact |
|---------|--------|
| **Dimension mismatch** | Schema says `Vector(1536)` but `nomic-embed-text` outputs 768-dim — latent config issue |
| **No HNSW index** | Only IVFFlat — HNSW would be a free perf win |
| **Jina MRL unused** | Jina v3 supports `dimensions` param for Matryoshka embeddings but AGENT-33 doesn't pass it |
| **Jina binary unused** | Jina v3 supports `encoding_type: "binary"` — not used |
| **Skills use BM25 only** | `SkillMatcher` has no embedding search — potential future integration |
| **Ollama KV quant available** | `OLLAMA_KV_CACHE_TYPE=q8_0` — zero-code win, just config |

### 4.3 Integration Surfaces

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATION ARCHITECTURE                      │
│                                                                  │
│  ┌─────────────┐    ┌──────────────────┐    ┌────────────────┐  │
│  │ Embedding    │───▶│ TurboQuant       │───▶│ Quantized      │  │
│  │ Provider     │    │ Compressor       │    │ Cache (LRU)    │  │
│  │ (Ollama/Jina)│    │ (NEW module)     │    │ 8-16× smaller  │  │
│  └─────────────┘    └────────┬─────────┘    └────────────────┘  │
│                              │                                   │
│                    ┌─────────▼──────────┐                       │
│                    │ Dual Storage        │                       │
│                    │ ┌────────────────┐  │                       │
│                    │ │pgvector (full) │  │  ← exact reranking   │
│                    │ └────────────────┘  │                       │
│                    │ ┌────────────────┐  │                       │
│                    │ │FAISS/mmap      │  │  ← fast prefilter    │
│                    │ │(4-bit SQ+rot)  │  │                       │
│                    │ └────────────────┘  │                       │
│                    └────────────────────┘                       │
│                                                                  │
│  ┌─────────────┐    ┌──────────────────┐                       │
│  │ Ollama       │    │ OLLAMA_KV_CACHE  │  ← infrastructure    │
│  │ Server       │    │ _TYPE=q8_0       │     config only       │
│  └─────────────┘    └──────────────────┘                       │
│                                                                  │
│  ┌─────────────┐    ┌──────────────────┐                       │
│  │ HybridSearch │───▶│ 3-Way RRF        │                       │
│  │ (BM25+Vec)   │    │ +Quantized ANN   │  ← search fusion     │
│  └─────────────┘    └──────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Storage Impact Analysis

### 5.1 Per-Vector Memory (1536-dim)

| Precision | Bytes/Vector | 100K Vectors | 1M Vectors | Compression |
|-----------|-------------|-------------|------------|-------------|
| float32 (current) | 6,144 | 614 MB | 6.1 GB | 1× |
| float16 (halfvec) | 3,072 | 307 MB | 3.0 GB | 2× |
| int8 (8-bit SQ) | 1,536 | 154 MB | 1.5 GB | 4× |
| **int4 (4-bit SQ)** | **768** | **77 MB** | **768 MB** | **8×** |
| int2 (2-bit SQ) | 384 | 38 MB | 384 MB | 16× |
| binary (1-bit) | 192 | 19 MB | 192 MB | 32× |

### 5.2 LRU Cache Impact

Current: 1024 entries × 6,144 bytes = **6.1 MB**  
With 4-bit SQ: 1024 entries × 768 bytes = **768 KB** (8× reduction)  
Allows **8× more entries** at same memory budget = better hit rate

---

## 6. Reference Implementations for Adaptation

### 6.1 Tier 1 — Critical References

| Repo | Purpose | Why |
|------|---------|-----|
| `Dao-AILab/fast-hadamard-transform` | CUDA Hadamard kernels | Flash Attention team; fused with PyTorch |
| `facebookresearch/faiss` | PQ/OPQ/SQ indices | Gold standard; `OPQMatrix` = TurboQuant rotation |
| `vllm-project/vllm` | KV cache quant kernels | PagedAttention + FP8/INT8 KV |
| `bitsandbytes-foundation/bitsandbytes` | Scalar quant CUDA kernels | Blockwise 4/8-bit, production-grade |
| `jy-yuan/KIVI` | KV cache baseline | Direct TurboQuant baseline |
| `SqueezeAILab/KVQuant` | KV cache research | Most comprehensive academic impl |
| `amirzandieh/QJL` | QJL official code | 1-bit JL transform, CUDA kernels |

### 6.2 Tier 2 — Strong References

| Repo | Purpose |
|------|---------|
| `cornell-relaxml/quip-sharp` | Hadamard + incoherence for weight VQ |
| `NVIDIA/TensorRT-LLM` | Production INT4/INT8/FP8 kernels |
| `mit-han-lab/llm-awq` | Per-channel AWQ CUDA kernels |
| `Vahe1994/AQLM` | Additive multi-codebook VQ for LLMs |
| `lucidrains/vector-quantize-pytorch` | Clean PyTorch VQ implementations |
| `rapidsai/cuml` | GPU-native JL random projection |

---

## 7. Recommended Adaptation Roadmap

### Phase 1: Infrastructure Quick Wins (Zero Code Changes)

```yaml
# docker-compose.yml — Ollama KV cache quantization
services:
  ollama:
    environment:
      OLLAMA_KV_CACHE_TYPE: q8_0          # 50% KV cache savings
      OLLAMA_FLASH_ATTENTION: "1"         # Required for KV quant
      OLLAMA_NUM_PARALLEL: "4"            # More parallel requests
```

- [ ] Enable `OLLAMA_KV_CACHE_TYPE=q8_0` in docker-compose
- [ ] Add HNSW index to pgvector (single SQL migration)
- [ ] Fix embedding dimension config mismatch (1536 vs 768)

### Phase 2: Embedding Compression Module

New module: `engine/src/agent33/memory/quantized_index.py`

**Core components:**
1. `RotationPreprocessor` — Randomized Hadamard (or QR for non-power-of-2 dims)
2. `ScalarQuantizer` — Per-dimension uniform quantization (2/4/8-bit)
3. `QuantizedVectorIndex` — In-memory sidecar index with mmap persistence
4. `BitPacker` — Sub-byte integer packing (4 values per byte at 2-bit)

**Integration points:**
- `EmbeddingCache` → store quantized embeddings (8× more entries)
- `LongTermMemory.store()` → dual-write to pgvector + quantized index
- `HybridSearcher` → 3-way RRF fusion (pgvector + BM25 + quantized ANN)

**Config additions to `config.py`:**
```python
quantized_index_enabled: bool = False
quantized_index_bits: int = 4        # 2, 4, or 8
quantized_index_rotation_seed: int = 42
quantized_index_prefilter_k: int = 50
quantized_index_storage_path: str = "var/quantized_index"
```

### Phase 3: FAISS-Backed Production Index

Replace custom `QuantizedVectorIndex` with FAISS for production scale:

```python
import faiss

# TurboQuant-equivalent FAISS pipeline
opq = faiss.OPQMatrix(d, d)            # Rotation preprocessing
sq = faiss.IndexIVFScalarQuantizer(
    faiss.IndexFlatL2(d), d, nlist=100,
    faiss.ScalarQuantizer.QT_4bit       # 4-bit per dimension
)
index = faiss.IndexPreTransform(opq, sq)
```

### Phase 4: Advanced TurboQuant Features

1. **PolarQuant**: Polar coordinate decomposition → direction + magnitude
2. **QJL residual**: 1-bit error correction stage
3. **Asymmetric distance computation**: Full-precision query × quantized DB
4. **Progressive quantization**: Layer 1 (index) at 2-bit, Layer 3 (full) at float32
5. **Jina binary embeddings**: Enable `encoding_type: "binary"` for coarse search

### Phase 5: Custom Inference Integration

If AGENT-33 moves to self-hosted inference (vLLM/TensorRT-LLM):
1. FP8 KV cache via vLLM `--kv-cache-dtype fp8_e5m2`
2. Custom Triton kernels for TurboQuant-style KV compression
3. Integration with Flash Attention 3 for fused quantized attention

---

## 8. Key Implementation Pseudocode

### 8.1 TurboQuant Encode/Decode

```python
def turboquant_encode(x: np.ndarray, seed: int, b_dir: int = 2, m_qjl: int = None):
    d = x.shape[-1]
    m_qjl = m_qjl or d // 2
    
    # Stage 0: Random rotation (Randomized Hadamard)
    signs = np.random.RandomState(seed).choice([-1, 1], d).astype(np.float32)
    y = fast_hadamard_transform(x * signs)
    
    # Stage 1: PolarQuant
    norm = np.linalg.norm(y)
    y_dir = y / (norm + 1e-10)
    q_norm = np.float16(norm)
    q_dir = np.round(y_dir * (2**(b_dir-1) - 1)).astype(np.int8)
    
    # Stage 1 reconstruction
    y_recon = float(q_norm) * q_dir.astype(np.float32) / (2**(b_dir-1) - 1)
    y_recon = y_recon * (norm / (np.linalg.norm(y_recon) + 1e-10))
    
    # Stage 2: QJL residual
    residual = y - y_recon
    rng = np.random.RandomState(seed + 1)
    qjl_bits = np.zeros(m_qjl, dtype=np.int8)
    for i in range(m_qjl):
        g = rng.randn(d).astype(np.float32) / np.sqrt(d)
        qjl_bits[i] = np.sign(residual @ g)
    
    return q_norm, q_dir, qjl_bits


def turboquant_decode(q_norm, q_dir, qjl_bits, seed, d, b_dir=2):
    m_qjl = len(qjl_bits)
    
    # Stage 1 reconstruct
    y_recon = float(q_norm) * q_dir.astype(np.float32) / (2**(b_dir-1) - 1)
    
    # Stage 2 QJL correction
    alpha = np.sqrt(2/np.pi) * float(q_norm) * 0.1  # estimated residual scale
    rng = np.random.RandomState(seed + 1)
    correction = np.zeros(d, dtype=np.float32)
    for i in range(m_qjl):
        g = rng.randn(d).astype(np.float32) / np.sqrt(d)
        correction += qjl_bits[i] * g
    correction *= alpha / m_qjl
    
    y_corrected = y_recon + correction
    
    # Inverse rotation
    signs = np.random.RandomState(seed).choice([-1, 1], d).astype(np.float32)
    x_hat = inverse_hadamard_transform(y_corrected) * signs
    return x_hat
```

### 8.2 Practical AGENT-33 Integration (Simplified)

```python
# engine/src/agent33/memory/quantized_index.py (simplified)

class TurboQuantCompressor:
    """TurboQuant-style rotation + scalar quantization for embeddings."""
    
    def __init__(self, dim: int = 768, bits: int = 4, seed: int = 42):
        self.dim = dim
        self.bits = bits
        self.levels = 2 ** bits - 1
        self.R = self._build_rotation(dim, seed)
        self.mins = None  # Fitted per-dimension
        self.scales = None
    
    def _build_rotation(self, d, seed):
        rng = np.random.RandomState(seed)
        H = rng.randn(d, d).astype(np.float32)
        Q, R = np.linalg.qr(H)
        return Q @ np.diag(np.sign(np.diag(R)))
    
    def fit(self, vectors: np.ndarray):
        rotated = vectors @ self.R.T
        self.mins = rotated.min(axis=0)
        self.scales = (rotated.max(axis=0) - self.mins) / self.levels
        self.scales[self.scales == 0] = 1.0
    
    def encode(self, vector: np.ndarray) -> np.ndarray:
        rotated = vector @ self.R.T
        normalized = (rotated - self.mins) / self.scales
        return np.clip(np.round(normalized), 0, self.levels).astype(np.uint8)
    
    def decode(self, codes: np.ndarray) -> np.ndarray:
        dequantized = codes.astype(np.float32) * self.scales + self.mins
        return dequantized @ self.R  # inverse rotation
    
    def approximate_distance(self, query: np.ndarray, codes: np.ndarray) -> np.ndarray:
        """Asymmetric distance: full-precision query vs quantized DB."""
        q_rotated = query @ self.R.T
        db_dequantized = codes.astype(np.float32) * self.scales + self.mins
        return np.linalg.norm(db_dequantized - q_rotated, axis=1)
```

---

## 9. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| No official TurboQuant code | Medium | Build on FAISS OPQ+SQ (equivalent algorithm) and QJL official repo |
| Recall degradation at low bits | Low | Use as prefilter, rerank with full-precision pgvector |
| Added complexity | Medium | Feature-flag everything; quantized index is optional sidecar |
| Dimension mismatch (1536 vs 768) | High | Fix config before any quant work — prerequisite |
| FAISS dependency size | Low | `faiss-cpu` is 30MB; only needed if quantized index enabled |

---

## 10. References

### Papers
1. **TurboQuant**: Zandieh et al. "TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate" (arXiv:2504.19874, ICLR 2026)
2. **PolarQuant**: arXiv:2502.02617 (AISTATS 2026)
3. **QJL**: Zandieh, Han, Daliri, Karbasi. "QJL: 1-Bit Quantized JL Transform for KV Cache Quantization with Zero Overhead" (AAAI 2025, arXiv:2406.03462)
4. **KIVI**: Liu et al. "KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache" (2024)
5. **KVQuant**: Hooper et al. "KVQuant: Towards 10 Million Context Length LLM Inference with KV Cache Quantization" (UC Berkeley, 2024)
6. **QuIP#**: Tseng et al. "QuIP#: Even Better LLM Quantization with Hadamard Incoherence and Lattice Codebooks" (Cornell, 2024)
7. **AWQ**: Lin et al. "AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration" (MIT, 2024)

### Key Repositories
- TurboQuant: *No official implementation* — use FAISS OPQ+SQ as equivalent
- QJL: https://github.com/amirzandieh/QJL
- KIVI: https://github.com/jy-yuan/KIVI
- KVQuant: https://github.com/SqueezeAILab/KVQuant
- FAISS: https://github.com/facebookresearch/faiss
- Fast Hadamard: https://github.com/Dao-AILab/fast-hadamard-transform
- vLLM: https://github.com/vllm-project/vllm
- bitsandbytes: https://github.com/bitsandbytes-foundation/bitsandbytes
