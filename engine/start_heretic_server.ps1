$ErrorActionPreference = "Stop"

$EngineDir = "d:\GITHUB\AGENT33\engine"
$ModelPath = "$EngineDir\models\Qwen3-Coder-Next-Q4_K_M.gguf"
$LlamaServer = "$EngineDir\bin\llama-cpp\llama-server.exe"

if (-Not (Test-Path $ModelPath)) {
    Write-Error "Error: Model not found at $ModelPath. Is it still downloading?"
    exit 1
}

if (-Not (Test-Path $LlamaServer)) {
    Write-Error "Error: llama-server.exe not found at $LlamaServer."
    exit 1
}

Write-Host "🚀 Launching Qwen3-Coder-Next (80B MoE) with Tensor Offloading..." -ForegroundColor Cyan

& $LlamaServer `
    -m "$ModelPath" `
    --jinja `
    -np 1 `
    -t 8 `
    -b 2048 `
    -ub 2048 `
    -c 80000 `
    -ngl 99 `
    -fa on `
    -n 4096 `
    --top-p 1.0 `
    --top-k 40 `
    --min-p 0.01 `
    --repeat-penalty 1.1 `
    --temp 0.2 `
    --host "0.0.0.0" `
    --port 8033 `
    --cache-type-k "q4_0" `
    --cache-type-v "q4_0" `
    -ot "blk\.[2-6][0-9]\.ffn_.*exps=CPU" `
    --no-mmap `
    --mlock
