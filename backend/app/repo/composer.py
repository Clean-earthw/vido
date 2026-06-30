"""Final-MP4 composition via system ffmpeg."""

import hashlib
import logging
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple
from urllib.parse import urlparse

from genblaze_core.media import Mp4Handler
from genblaze_core.models.asset import Asset

from app.repo.pipelines import backend, PREFIX
from app.types.storyboard import StoryboardSpec

logger = logging.getLogger("api.composer")

_FFMPEG_TIMEOUT_SEC = 300
_CANVAS_W, _CANVAS_H, _FPS = 1280, 720, 30


@dataclass
class _SceneBundle:
    index: int
    video_path: Path | None
    still_path: Path | None
    narration_path: Path | None
    duration: float


def _asset_url_or_none(step) -> str | None:
    assets = getattr(step, "assets", None) or []
    return assets[0].url if assets else None


def _key_from_asset_url(url: str) -> str:
    path = urlparse(url).path.lstrip("/")
    _, _, key = path.partition("/")
    return key or path


def _download(key_or_url: str, dest: Path) -> Path:
    key = _key_from_asset_url(key_or_url) if key_or_url.startswith("http") else key_or_url
    dest.parent.mkdir(parents=True, exist_ok=True)
    blob = backend().get(key)
    dest.write_bytes(blob)
    logger.info("downloaded asset", extra={
        "key": key,
        "size_bytes": len(blob),
        "dest": str(dest.name),
    })
    return dest


def _group_scenes(b2_run, b1_run, spec: StoryboardSpec, tmp: Path) -> List[_SceneBundle]:
    """Pair each scene with its (video|keyframe-still, narration) assets."""
    steps = b2_run.run.steps
    kf_steps = b1_run.run.steps
    bundles = []
    
    for i, scene in enumerate(spec.scenes):
        vi, ti = 2 * i, 2 * i + 1
        
        video_path = still_path = None
        video_url = _asset_url_or_none(steps[vi]) if vi < len(steps) else None
        
        if video_url is not None:
            video_path = _download(video_url, tmp / f"scene_{i:02d}.mp4")
        else:
            kf_url = _asset_url_or_none(kf_steps[i]) if i < len(kf_steps) else None
            if kf_url is None:
                raise RuntimeError(f"scene {i}: no video clip and no keyframe still")
            still_path = _download(kf_url, tmp / f"scene_{i:02d}_still.png")
            logger.info("scene video fell back to keyframe still", extra={
                "scene_index": i,
                "video_step_index": vi,
            })
        
        narration_url = _asset_url_or_none(steps[ti]) if ti < len(steps) else None
        bundles.append(_SceneBundle(
            index=i,
            video_path=video_path,
            still_path=still_path,
            narration_path=(
                _download(narration_url, tmp / f"scene_{i:02d}_voice.wav")
                if narration_url else None
            ),
            duration=scene.duration_sec,
        ))
    
    return bundles


def _music_url(b2_run) -> str | None:
    steps = b2_run.run.steps
    if not steps:
        return None
    return _asset_url_or_none(steps[-1])


def _download_music(b2_run, tmp: Path) -> Path | None:
    url = _music_url(b2_run)
    return _download(url, tmp / "music.wav") if url else None


def degradation_notices(scenes: List[_SceneBundle], music_present: bool) -> List[str]:
    notices = []
    still = [s.index for s in scenes if s.video_path is None]
    if still:
        nums = ", ".join(str(i + 1) for i in still)
        notices.append(f"Video unavailable for scene(s) {nums} — used keyframe still")
    
    missing = [s.index for s in scenes if s.narration_path is None]
    if missing:
        if len(missing) == len(scenes):
            notices.append("Narration unavailable — final video has no voiceover")
        else:
            nums = ", ".join(str(i + 1) for i in missing)
            notices.append(f"Narration unavailable for scene(s) {nums}")
    
    if not music_present:
        notices.append("Background music unavailable — final video has no score")
    
    return notices


def _run_ffmpeg(args: List[str], *, stage: str) -> None:
    argv0 = " ".join(args[:8]) + (" ..." if len(args) > 8 else "")
    logger.info("ffmpeg start", extra={"stage": stage, "argv0": argv0})
    
    start = time.perf_counter()
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args],
            check=True,
            timeout=_FFMPEG_TIMEOUT_SEC,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or b"").decode("utf-8", errors="replace")
        logger.error("ffmpeg failed", extra={
            "stage": stage,
            "argv0": argv0,
            "duration_ms": int((time.perf_counter() - start) * 1000),
            "stderr": stderr.strip()[-2000:],
        })
        raise RuntimeError(f"ffmpeg {stage} failed: {stderr.strip()}") from exc
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg timeout", extra={"stage": stage, "argv0": argv0})
        raise
    
    logger.info("ffmpeg ok", extra={
        "stage": stage,
        "duration_ms": int((time.perf_counter() - start) * 1000),
    })


_NORMALIZE = (
    f"scale={_CANVAS_W}:{_CANVAS_H}:force_original_aspect_ratio=decrease,"
    f"pad={_CANVAS_W}:{_CANVAS_H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={_FPS}"
)


def _concat_video(scenes: List[_SceneBundle], tmp: Path) -> Path:
    inputs = []
    filters = []
    labels = []
    
    for idx, s in enumerate(scenes):
        if s.video_path is not None:
            inputs += ["-i", str(s.video_path)]
        else:
            inputs += ["-loop", "1", "-t", str(s.duration), "-i", str(s.still_path)]
        filters.append(f"[{idx}:v]{_NORMALIZE}[v{idx}]")
        labels.append(f"[v{idx}]")
    
    filters.append(f"{''.join(labels)}concat=n={len(scenes)}:v=1:a=0[outv]")
    out = tmp / "video.mp4"
    
    _run_ffmpeg(
        [*inputs, "-filter_complex", ";".join(filters),
         "-map", "[outv]", "-c:v", "libx264", "-preset", "ultrafast",
         "-pix_fmt", "yuv420p", "-an", str(out)],
        stage="concat",
    )
    return out


def _mix_audio(scenes: List[_SceneBundle], music_path: Path | None, tmp: Path) -> Path | None:
    inputs = []
    filters = []
    mix_labels = []
    ff_idx = 0
    offset_ms = 0
    
    for s in scenes:
        if s.narration_path is not None:
            inputs += ["-i", str(s.narration_path)]
            filters.append(f"[{ff_idx}:a]adelay={offset_ms}|{offset_ms}[v{ff_idx}]")
            mix_labels.append(f"[v{ff_idx}]")
            ff_idx += 1
        offset_ms += int(s.duration * 1000)
    
    if music_path is not None:
        inputs += ["-i", str(music_path)]
        gain = "-18dB" if mix_labels else "0dB"
        filters.append(f"[{ff_idx}:a]volume={gain}[mus]")
        mix_labels.append("[mus]")
        ff_idx += 1
    
    if not mix_labels:
        return None
    
    filters.append(
        f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}"
        ":duration=longest:dropout_transition=0[aout]"
    )
    out = tmp / "audio.m4a"
    
    _run_ffmpeg(
        [*inputs, "-filter_complex", ";".join(filters),
         "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", str(out)],
        stage="mix-audio",
    )
    return out


def _finalize(video: Path, audio: Path | None, tmp: Path) -> Path:
    out = tmp / "final.mp4"
    inputs = ["-i", str(video)]
    audio_idx = None
    
    if audio is not None:
        inputs += ["-i", str(audio)]
        audio_idx = 1
    
    args = [*inputs, "-map", "0:v", "-c:v", "copy"]
    
    if audio_idx is not None:
        args += ["-map", f"{audio_idx}:a", "-c:a", "copy"]
    else:
        args += ["-an"]
    
    args += ["-movflags", "+faststart", str(out)]
    _run_ffmpeg(args, stage="finalize")
    return out


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compose_final(b2_run, b1_run, spec: StoryboardSpec) -> tuple[Asset, List[str]]:
    """Concat scenes, mix audio, upload to B2."""
    
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg binary not found on PATH")
    
    run_id = b2_run.run.run_id
    start = time.perf_counter()
    
    with tempfile.TemporaryDirectory(prefix="genblaze-compose-") as tmp_str:
        tmp = Path(tmp_str)
        scenes = _group_scenes(b2_run, b1_run, spec, tmp)
        music_path = _download_music(b2_run, tmp)
        notices = degradation_notices(scenes, music_path is not None)
        
        logger.info("compose start", extra={
            "run_id": run_id,
            "scene_count": len(spec.scenes),
            "total_duration_sec": spec.total_duration_sec,
            "degradation_notices": notices,
        })
        
        video_only = _concat_video(scenes, tmp)
        audio_mix = _mix_audio(scenes, music_path, tmp)
        final_path = _finalize(video_only, audio_mix, tmp)
        
        # Embed manifest if available
        try:
            Mp4Handler().embed(final_path, b2_run.manifest)
        except Exception as exc:
            logger.warning("manifest embed failed", extra={"run_id": run_id, "exception": str(exc)})
        
        final_bytes = final_path.read_bytes()
        key = f"{PREFIX}/{run_id}/final.mp4"
        backend().put(key, final_bytes, content_type="video/mp4")
        
        logger.info("compose ok", extra={
            "run_id": run_id,
            "key": key,
            "size_bytes": len(final_bytes),
            "duration_ms": int((time.perf_counter() - start) * 1000),
        })
        
        return Asset(
            url=backend().get_durable_url(key),
            media_type="video/mp4",
            sha256=_sha256(final_bytes),
            size_bytes=len(final_bytes),
        ), notices