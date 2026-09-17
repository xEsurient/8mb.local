#!/usr/bin/env sh
# Docker entrypoint: set up NVIDIA environment, then launch supervisord.

log() {
  ts=$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date)
  echo "[entrypoint] $ts $*"
}

# Ensure NVIDIA library paths are available
for libdir in /usr/local/nvidia/lib64 /usr/local/nvidia/lib /usr/local/cuda/lib64 /usr/lib/wsl/lib; do
  if [ -d "$libdir" ]; then
    case ":${LD_LIBRARY_PATH:-}:" in
      *:"$libdir":*) ;;
      *) export LD_LIBRARY_PATH="${libdir}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" ;;
    esac
  fi
done

# Dynamic defaults for CPU encoding
if [ -z "$WORKER_CONCURRENCY" ]; then
  # On Apple Silicon 8-12 cores is common, leave some breathing room
  cores=$(nproc)
  export WORKER_CONCURRENCY=$(( cores > 2 ? cores - 1 : 1 ))
  log "Set WORKER_CONCURRENCY to $WORKER_CONCURRENCY based on $cores CPU cores"
fi

# Ensure volumes have correct permissions for unprivileged users
chown -R redis:redis /var/lib/redis 2>/dev/null || true
chown -R redis:redis /var/log/redis 2>/dev/null || true

# Add appuser if not exists
if ! id "appuser" >/dev/null 2>&1; then
    useradd -r -M -s /bin/false appuser || true
fi

# We use chown -R carefully, as directories might have lots of files. 
# In reality, just setting the top-level directory ownership is usually enough if it's a bind mount.
chown appuser:appuser /app/uploads /app/outputs /app/data 2>/dev/null || true

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf "$@"
