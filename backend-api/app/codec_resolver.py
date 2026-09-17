"""Shared backend resolver for effective capability and default codec selection."""

import os
import urllib.request
import json
import logging
import time
from typing import Dict, Any

from . import settings_manager
from .deps import get_hw_info_cached

logger = logging.getLogger(__name__)

DAEMON_TIMEOUT = 0.5
NON_DAEMON_CODECS = {'libx264', 'libx265', 'libsvtav1', 'libaom-av1', 'h264_nvenc', 'hevc_nvenc', 'av1_nvenc'}

_daemon_cache = {"ts": 0.0, "state": {"ready": False, "codecs": []}}

def probe_daemon() -> Dict[str, Any]:
    """Probe the native macOS daemon for capabilities in a non-blocking way with a short cache."""
    now = time.time()
    if now - _daemon_cache["ts"] < 2.0:
        return _daemon_cache["state"]

    daemon_url = os.getenv("DAEMON_URL", "")
    if not daemon_url:
        daemon_address = settings_manager.get_daemon_port()
        if str(daemon_address).isdigit():
            daemon_url = f"http://host.docker.internal:{daemon_address}"
        else:
            daemon_url = f"http://{daemon_address}" if "://" not in daemon_address else daemon_address

    state = {"ready": False, "codecs": []}
    try:
        req = urllib.request.Request(f"{daemon_url.rstrip('/')}/health", method="GET")
        req.add_header("X-API-Key", os.getenv("DAEMON_API_KEY", ""))
        with urllib.request.urlopen(req, timeout=DAEMON_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get("status") == "ok":
                state = {
                    "ready": True,
                    "codecs": data.get("codecs", [])
                }
    except Exception as e:
        pass
    
    _daemon_cache["ts"] = now
    _daemon_cache["state"] = state
    return state


def get_effective_capabilities() -> Dict[str, Any]:
    """
    Returns the effective capability snapshot:
    - daemon state
    - worker hardware encoders
    - effective visible codecs
    - effective default codec
    - user visibility overrides (raw)
    """
    hw_info = get_hw_info_cached() or {}
    hw_type = hw_info.get("type", "cpu")
    avail_encoders = hw_info.get("available_encoders", {}) or {}

    daemon_state = probe_daemon()
    daemon_ready = daemon_state["ready"]
    daemon_codecs = daemon_state["codecs"]

    # 1. Start with capabilities (what the system can actually do)
    capable_codecs = set()
    
    # Add hardware encoders (NVENC)
    if hw_type == "nvidia":
        for enc in avail_encoders.values():
            capable_codecs.add(enc)
            
    # Always capable of CPU encoders
    capable_codecs.update({'libx264', 'libx265', 'libsvtav1', 'libaom-av1'})
    
    # Add daemon encoders if ready
    if daemon_ready:
        for c in daemon_codecs:
            if c in ("hevc_videotoolbox", "h264_videotoolbox"):
                capable_codecs.add(c)

    # 2. Apply Visibility Overrides
    raw_vis = settings_manager.get_raw_codec_visibility()
    
    # Default policy:
    # If daemon is ready, NON_DAEMON_CODECS are hidden by default unless explicitly enabled.
    visible_codecs = []
    
    # Insert daemon codecs first (HEVC > H264)
    if "hevc_videotoolbox" in capable_codecs and raw_vis.get("hevc_videotoolbox", True):
        visible_codecs.append("hevc_videotoolbox")
    if "h264_videotoolbox" in capable_codecs and raw_vis.get("h264_videotoolbox", True):
        visible_codecs.append("h264_videotoolbox")

    # Add other codecs
    # Order: NVENC AV1 > HEVC > H264 > CPU
    other_priority = ["av1_nvenc", "hevc_nvenc", "h264_nvenc", "libsvtav1", "libaom-av1", "libx265", "libx264"]
    for c in other_priority:
        if c in capable_codecs:
            settings_key = c.replace('-', '_')
            if daemon_ready:
                # Must be explicitly enabled
                if raw_vis.get(settings_key, False):
                    visible_codecs.append(c)
            else:
                # Follow normal visibility settings (defaults to True if not in raw_vis)
                if raw_vis.get(settings_key, True):
                    visible_codecs.append(c)

    # 3. Determine Effective Default Codec
    data = settings_manager._ensure_defaults()
    profiles = data.get('preset_profiles', [])
    default_name = data.get('default_preset')
    
    saved_default_codec = None
    for p in profiles:
        if p.get('name') == default_name:
            saved_default_codec = p.get('video_codec')
            break
            
    effective_default_codec = None
    # If the saved default codec is visible and capable, use it.
    if saved_default_codec and saved_default_codec in visible_codecs:
        effective_default_codec = saved_default_codec
    else:
        # Normalize to the best visible codec
        if visible_codecs:
            effective_default_codec = visible_codecs[0]
            
    # Ensure profile matches
    effective_default_preset_name = None
    if effective_default_codec:
        for p in profiles:
            if p.get("video_codec") == effective_default_codec:
                effective_default_preset_name = p.get("name")
                break
        
        # If no profile exists for this codec, pick the first available profile
        if not effective_default_preset_name and profiles:
            for p in profiles:
                if p.get("video_codec") in visible_codecs:
                    effective_default_preset_name = p.get("name")
                    break

    return {
        "daemon_ready": daemon_ready,
        "daemon_codecs": daemon_codecs,
        "worker_hardware_type": hw_type,
        "worker_available_encoders": avail_encoders,
        "capable_codecs": list(capable_codecs),
        "visible_codecs": visible_codecs,
        "effective_default_codec": effective_default_codec,
        "effective_default_preset_name": effective_default_preset_name,
        "raw_visibility": raw_vis
    }
