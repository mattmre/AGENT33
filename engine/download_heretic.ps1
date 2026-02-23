$ErrorActionPreference = "Stop"
$WorkingDir = "d:\GITHUB\AGENT33\engine"

# Dynamically fetch the latest llama.cpp CUDA build
Write-Host "Querying GitHub for latest llama.cpp release..."
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Release = Invoke-RestMethod -Uri "https://api.github.com/repos/ggerganov/llama.cpp/releases/latest"
$Asset = $Release.assets | Where-Object { $_.name -match "bin-win-cuda-cu12.2-x64.zip" -or $_.name -match "bin-win-cuda-cu12.1-x64.zip" -or $_.name -match "bin-win-cuda-cu12.0-x64.zip" } | Select-Object -First 1

if (-Not $Asset) {
    # Fallback if specific cuda versions change naming convention
    $Asset = $Release.assets | Where-Object { $_.name -match "bin-win.*cuda.*x64.zip" } | Select-Object -First 1
}

$LlamaZipUrl = $Asset.browser_download_url
$LlamaZipDist = "$WorkingDir\bin\llama.zip"
$LlamaBinDir = "$WorkingDir\bin\llama-cpp"

if (-Not (Test-Path "$LlamaBinDir\llama-server.exe")) {
    Write-Host "Downloading llama.cpp latest ($LlamaZipUrl)..."
    Invoke-WebRequest -Uri $LlamaZipUrl -OutFile $LlamaZipDist
    Write-Host "Extracting..."
    Expand-Archive -Path $LlamaZipDist -DestinationPath $LlamaBinDir -Force
    Remove-Item $LlamaZipDist
}
else {
    Write-Host "llama.cpp already downloaded."
}

# Downloading the 45.5 GB model directly via HTTPS
Write-Host "Starting 45GB Model Download... This will take a while!"
$ModelDir = "$WorkingDir\models"
$ModelUrl = "https://huggingface.co/unsloth/Qwen3-Coder-Next-GGUF/resolve/main/Qwen3-Coder-Next-Q4_K_M.gguf?download=true"
$ModelFile = "$ModelDir\Qwen3-Coder-Next-Q4_K_M.gguf"

if (-Not (Test-Path $ModelFile)) {
    Write-Host "Executing BITS Transfer for 45GB file. Check the file size in the /models folder to track progress!"
    Start-BitsTransfer -Source $ModelUrl -Destination $ModelFile -Priority Foreground
}
else {
    Write-Host "Model file already exists!"
}

Write-Host "All downloads complete!"
