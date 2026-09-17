# 8mb.local

8mb.local is a privacy-first, LAN-native video compression and management service. It uses hardware-accelerated encoding (NVIDIA NVENC on Linux/Windows via CUDA, or optional macOS native daemon offloading) alongside CPU fallback encoders (SVT-AV1, x264, x265) to optimally compress high-resolution video into targeted byte sizes. 

## Features

- **Strict Target Sizes**: Intelligently calculates exact bitrates to hit specific byte constraints (e.g., 8.00MB for Discord, 25MB, 50MB, etc.).
- **Hardware Acceleration**: 
  - NVIDIA GPUs (NVENC) are fully supported via the default GPU container. 
  - macOS Silicon (Apple VideoToolbox) is supported via an optional native background daemon (`daemon/`).
- **CPU Fallbacks**: If hardware encoding fails or hardware is not present, it seamlessly falls back to CPU encoding using highly optimized `libsvtav1`, `libx264`, or `libx265`.
- **LAN-Native & Privacy First**: By design, no external requests are made. All assets (fonts, JS) are self-hosted. 
- **Durable Job Management**: Backed by Celery and Redis. Full support for batch tracking, pausing, resuming, and transactional cancellation.

## Getting Started

### Prerequisites

- **Docker** and **Docker Compose**
- *(Optional, for NVIDIA GPUs)*: [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed on the host.

### Starting the Service

By default, `docker-compose.yml` attempts to use the NVIDIA GPU and runs on port `8001`.

```bash
docker compose up -d
```

If you do not have an NVIDIA GPU, or the above fails, you can use the CPU-only configuration:

```bash
docker compose -f docker-compose.cpu.yml up -d
```

The service will be available at `http://localhost:8001` or `http://<your-lan-ip>:8001`.

## Configuration & Security

8mb.local prioritizes a seamless LAN experience but can be secured if exposed to broader networks. Configuration is handled via environment variables in an optional `.env` file (or directly in your `docker-compose.yml`).

### No-Login Sharing (Default)
Out of the box, `8mb.local` operates in "No-Login Sharing" mode. Anyone on the local network who can access port `8001` can upload, compress, and download videos without a password. 

### Enabling Authentication
If you wish to secure your instance (e.g., if port 8001 is exposed beyond a trusted LAN):

1. Create a `.env` file in the project root.
2. Add the following variables:
   ```env
   AUTH_ENABLED=true
   AUTH_USER=admin
   AUTH_PASS=your_secure_password
   ```
3. Restart the container (`docker compose down && docker compose up -d`).

Once enabled, visitors will be prompted for Basic Authentication before accessing the UI or API.

> **Note:** The UI Settings page cannot enable authentication from a disabled state for security reasons (to prevent a public user from locking you out). It must be enabled via the `.env` file first.

### Config Precedence
Settings applied globally in the `Settings` UI override the default application behaviors. However, environmental variables (`.env`) override UI settings for critical infrastructure limits (like `WORKER_CONCURRENCY`). 

### Settings Migration (`settings.json`)
If you are migrating from an earlier version, your existing `settings.json` will be automatically migrated on startup to support visibility toggles for new VideoToolbox codecs. Additionally, codecs that are technically unsupported by the current execution environment (or the connected daemon) are now automatically hidden in the frontend without requiring you to manually maintain explicit visibility overrides. Note that if you explicitly uncheck a codec in the Settings UI, it will remain hidden globally even if your hardware supports it.

## Operations & Data

### File Formats and Target Units
- Supported input formats include nearly any video FFmpeg can read.
- Target constraints are calculated using binary megabytes (1 MB = 1,048,576 bytes) minus a small safety margin for container muxing overhead, ensuring outputs strictly fit into services with hard file size limits.

### Cancellation and Retention
- **Cancellation**: Canceling a job from the UI will instantly send a SIGTERM to the FFmpeg subprocess, release hardware resources, and forcefully clean up partial output files.
- **Retention**: Successfully processed files and their metadata are kept on disk according to your Retention Policy (configurable in the UI Settings). Once the retention period expires, the artifact and its Redis job history are purged.

### Restart Recovery
The system is designed to survive restarts. 
- All video uploads, outputs, and internal databases are bound to persistent volumes in `./data`, `./uploads`, and `./outputs`.
- Redis operates with AOF (Append-Only File) persistence enabled. Any jobs left in the queue during a container restart will automatically resume processing when the worker comes back online.

### Tests
To verify encoder and hardware availability, a suite of initialization tests is run automatically upon startup. If you wish to run backend tests manually, you can execute them within the worker directory:

```bash
docker exec -it 8mb.local bash -c "cd /app/worker && pytest tests/"
```

## Optional: macOS Daemon Offload

If you are running the service on a Mac and wish to utilize Apple Silicon VideoToolbox for hardware acceleration, you can install the provided background daemon on the host. The docker container will detect the local daemon and securely offload compatible compression jobs to it.

1. Ensure Homebrew is installed on your Mac.
2. Run the daemon installer script natively on the host:
   ```bash
   cd daemon
   ./install.sh
   ```
3. The installer will prompt for a port (default: `7998`) and automatically generate an API Key.
4. Copy the generated `DAEMON_API_KEY` from the installer output.
5. In your project `.env` file (alongside your `docker-compose.yml`), configure the connection:
   ```env
   DAEMON_URL=http://host.docker.internal:7998
   DAEMON_API_KEY=your_generated_api_key_here
   ```
6. Restart your docker containers so they pick up the API key.
   *(Ensure you bind it to `127.0.0.1` and not a public interface for security).*

---
*Built with FastAPI, SvelteKit, FFmpeg, and Celery.*
