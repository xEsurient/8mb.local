# Build notes — 8mb.local v136

**Release date:** 2026-04-17  

## Docker image

| Field | Value |
|--------|--------|
| **Registry** | Docker Hub |
| **Repository** | `jms1717/8mblocal` |
| **Tag** | `latest` (also aligns with app version **136**) |

## Build locally

From the repository root (after checkout of the release commit):

```bash
docker build \
  --build-arg BUILD_VERSION=136 \
  --build-arg BUILD_COMMIT="$(git rev-parse --short HEAD)" \
  -t jms1717/8mblocal:latest \
  .
```

Compose (CPU-only default):

```bash
docker compose up -d --build
```

With NVIDIA GPU passthrough:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

## Publish to Docker Hub

```bash
docker login
docker push jms1717/8mblocal:latest
```

## Verify

```bash
docker run --rm jms1717/8mblocal:latest cat /app/VERSION
curl -s http://127.0.0.1:8001/api/version   # after compose up; expect `"version":"136"`
```

## Release contents (summary)

See **[CHANGELOG.md](./CHANGELOG.md)** — **v136** includes portrait/display-matrix handling (full `ffprobe` + software decode when rotation is non-zero), optional **target video bitrate**, and the **default / GPU overlay** compose split.

---

## Build record

| Item | Value |
|------|--------|
| **Git commit** | `2484efa4aaa288eed5061255a3bdea145d24478b` (short: `2484efa`) |
| **Built by** | Local `docker build` matching this commit |
