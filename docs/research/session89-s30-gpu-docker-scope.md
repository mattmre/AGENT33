# S30: GPU/Custom-Image Docker Execution

## Status
Session 89 implementation.

## Goal
Extend the Docker execution adapter layer to support GPU hardware passthrough
(NVIDIA and AMD) and custom Docker image selection with configurable pull
policies.

## Architecture

### New module: `engine/src/agent33/execution/gpu.py`
- **GPURuntime** (StrEnum): NVIDIA, AMD, NONE
- **GPUConfig** (Pydantic model): runtime, device_ids, memory_limit, capabilities
- **CustomImageConfig** (Pydantic model): image, pull_policy, registry_auth, build_context
- **GPUDockerManager**: runtime detection, Docker arg building, image validation, GPU info

### Modified: `engine/src/agent33/execution/models.py`
- Added `gpu`, `custom_image`, `image_pull_policy` fields to `SandboxConfig`

### Modified: `engine/src/agent33/config.py`
- Added `execution_gpu_enabled`, `execution_default_docker_image`, `execution_gpu_runtime`
- Added field validator for `execution_gpu_runtime`

### New route: `engine/src/agent33/api/routes/execution.py`
- `GET /v1/execution/gpu-info` (agents:read scope) returns GPU availability and config

### Lifespan wiring: `engine/src/agent33/main.py`
- GPUDockerManager initialized and stored on `app.state.gpu_docker_manager`
- Execution route registered

## GPU Flag Generation

### NVIDIA
- `--gpus "device=<ids>,capabilities=<caps>"` for GPU access
- `-e NVIDIA_VISIBLE_DEVICES=<ids>` for compatibility
- `-e NVIDIA_DRIVER_CAPABILITIES=<caps>` when memory limit set
- `--shm-size <limit>` for shared memory

### AMD (ROCm)
- `--device /dev/dri/renderD<128+id>` for specific devices
- `--device /dev/kfd --device /dev/dri` for all devices
- `--group-add video` for GPU group access
- `-e ROC_ENABLE_PRE_VEGA=1` for broad compatibility

## Test Coverage
- GPUConfig model validation and serialization
- CustomImageConfig defaults and field behaviour
- SandboxConfig with new GPU fields
- GPUDockerManager.build_docker_args: no GPU, NVIDIA all/specific, AMD all/specific,
  memory limits, custom capabilities, custom images, combined configurations
- detect_gpu_runtime: NVIDIA, AMD, NONE, preference order
- validate_image: never/always/if-not-present policies
- get_gpu_info: no GPU, NVIDIA info, AMD info
- API route: GET /v1/execution/gpu-info response shape

## Configuration
| Setting | Default | Description |
|---------|---------|-------------|
| `execution_gpu_enabled` | `false` | Feature flag for GPU dispatch |
| `execution_default_docker_image` | `python:3.11-slim` | Default image when none specified |
| `execution_gpu_runtime` | `nvidia` | Preferred GPU runtime (nvidia, amd) |
