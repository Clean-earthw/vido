"""Genblaze pipeline factories with Google Gemini + GMICloud."""

import json
import logging
import re
import time
import uuid
from dataclasses import replace
from functools import lru_cache
from typing import Optional

from genblaze_core import (
    Asset,
    KeyStrategy,
    Modality,
    ObjectStorageSink,
    Pipeline,
    StepCache,
)
from genblaze_core.observability import CompositeTracer, LoggingTracer, OTelTracer
from genblaze_core.providers.model_registry import ModelRegistry
from genblaze_decart import DecartVideoProvider
from genblaze_elevenlabs import ElevenLabsTTSProvider
from genblaze_gmicloud import GMICloudAudioProvider, GMICloudVideoProvider, GMICloudImageProvider
from genblaze_gmicloud.models.audio import build_audio_registry
from genblaze_google import ImagenProvider
from genblaze_google.chat import chat as gemini_chat
from genblaze_nvidia import NvidiaAudioProvider
from genblaze_s3 import S3StorageBackend

from app.config import settings
from app.prompts.storyboard import build_storyboard_prompt
from app.types.storyboard import StoryboardSpec

PIPELINE_NAME = "genblaze-gen-media-multi-provider-sample"
PREFIX = "explainers"

logger = logging.getLogger("api.pipelines")


# --- Backend + sink singletons ----------------------------------------------

@lru_cache(maxsize=1)
def backend() -> S3StorageBackend:
    """Singleton backend — explicit kwargs bypass the library's B2_APP_KEY env fallback."""
    return S3StorageBackend.for_backblaze(
        settings.b2_bucket_name,
        region=settings.b2_region,
        key_id=settings.b2_key_id,
        app_key=settings.b2_application_key,
        auto_lifecycle=True,
    )


def sink() -> ObjectStorageSink:
    """Per-run hierarchical layout: `explainers/<run-id>/...`."""
    return ObjectStorageSink(backend(), prefix=PREFIX, key_strategy=KeyStrategy.HIERARCHICAL)


def _tracer() -> CompositeTracer:
    tracers = [LoggingTracer()]
    if settings.otel_endpoint:
        tracers.append(OTelTracer(endpoint=settings.otel_endpoint))
    return CompositeTracer(tracers)


def _attach(p: Pipeline) -> Pipeline:
    """Attach tracer + step-cache to every pipeline."""
    return p.tracer(_tracer()).cache(StepCache(settings.step_cache_dir))


def presign_asset_url(key_or_url: str, *, expires_in: int = 900) -> str:
    """Presign a key OR durable Manifest/Asset URL for B1→B2 image handoff."""
    if key_or_url.startswith("http"):
        key = backend().key_from_url(key_or_url)
        if key is None:
            logger.error("presign: unrecognized B2 URL", extra={"input": key_or_url})
            raise ValueError(f"Unrecognized B2 asset URL: {key_or_url}")
    else:
        key = key_or_url
    presigned = backend().get_url(key, expires_in=expires_in)
    logger.debug("presigned asset", extra={"key": key, "expires_in_sec": expires_in})
    return presigned


def probe_storage() -> bool:
    """Health check — True if the backend can reach the bucket."""
    try:
        backend().exists("__genblaze_health_probe__")
        return True
    except Exception:
        return False


# --- Stage A: storyboard planning with Google Gemini -----------------------

def generate_storyboard(
    prompt: str,
    style: str = "cinematic",
    voice: str = "professional",
    google_api_key: Optional[str] = None
) -> tuple[StoryboardSpec, str]:
    """Stage A — one-shot Google Gemini chat call with user-provided API key."""
    
    # Use provided key or fallback to settings
    api_key = google_api_key or settings.google_api_key
    
    if not api_key:
        raise ValueError("Google API key is required for Gemini storyboard generation")
    
    logger.info("storyboard generate start", extra={
        "model": settings.chat_model,
        "provider": "google/gemini",
        "prompt_chars": len(prompt),
        "prompt_preview": prompt[:240],
        "style": style,
        "voice": voice,
        "has_api_key": bool(api_key),
    })
    
    start = time.perf_counter()
    
    try:
        system_prompt = build_storyboard_prompt(prompt, style, voice)
        
        response = gemini_chat(
            settings.chat_model,
            prompt=system_prompt,
            api_key=api_key,
            temperature=settings.chat_temperature,
        )
    except Exception:
        logger.exception("storyboard chat failed", extra={
            "model": settings.chat_model,
            "duration_ms": int((time.perf_counter() - start) * 1000),
        })
        raise
    
    # Parse the JSON response manually
    try:
        spec_data = json.loads(response.text)
        spec = StoryboardSpec.model_validate(spec_data)
    except json.JSONDecodeError:
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response.text, re.DOTALL)
        if json_match:
            spec = StoryboardSpec.model_validate_json(json_match.group(1))
        else:
            json_match = re.search(r'(\{.*\})', response.text, re.DOTALL)
            if json_match:
                spec = StoryboardSpec.model_validate_json(json_match.group(1))
            else:
                logger.error("Failed to parse Gemini response as JSON", extra={
                    "response_preview": response.text[:500]
                })
                raise ValueError("Gemini response was not valid JSON")
    
    key = f"{PREFIX}/{uuid.uuid4().hex}/storyboard.json"
    backend().put(
        key,
        json.dumps(spec.model_dump(), indent=2).encode("utf-8"),
        content_type="application/json",
    )
    
    logger.info("storyboard generate ok", extra={
        "model": settings.chat_model,
        "provider": "google/gemini",
        "duration_ms": int((time.perf_counter() - start) * 1000),
        "title": spec.title,
        "style_prompt": spec.style_prompt,
        "scene_count": len(spec.scenes),
        "total_duration_sec": spec.total_duration_sec,
        "key": key,
    })
    
    return spec, key


# --- GMICloud providers with dynamic API key ------------------------------

def get_gmi_image_provider(api_key: str) -> GMICloudImageProvider:
    """Get GMICloud image provider with user-provided API key."""
    if not api_key:
        raise ValueError("GMICloud API key is required for image generation")
    return GMICloudImageProvider(api_key=api_key)


def get_gmi_video_provider(api_key: str) -> GMICloudVideoProvider:
    """Get GMICloud video provider with user-provided API key."""
    if not api_key:
        raise ValueError("GMICloud API key is required for video generation")
    return GMICloudVideoProvider(api_key=api_key)


def get_gmi_audio_provider(api_key: str) -> GMICloudAudioProvider:
    """Get GMICloud audio provider with user-provided API key."""
    if not api_key:
        raise ValueError("GMICloud API key is required for audio/music generation")
    return GMICloudAudioProvider(
        api_key=api_key,
        models=_instrumental_music_registry(),
    )


def _instrumental_music_registry() -> ModelRegistry:
    """Audio registry override for instrumental music."""
    reg = build_audio_registry()
    base = reg.get(settings.music_model)
    reg.register(replace(
        base,
        param_allowlist=(base.param_allowlist or frozenset()) | {"lyrics", "is_instrumental"},
        param_defaults={**dict(base.param_defaults), "lyrics": "[Inst]", "is_instrumental": True},
    ))
    return reg


# --- Stage B0: Reference image using GMICloud Image Provider ---------------

def build_reference_pipeline(spec: StoryboardSpec, gmi_api_key: str) -> Pipeline:
    """Stage B0 — generate a reference image using GMICloud Image Provider."""
    logger.info("build B0 pipeline", extra={
        "stage": "B0.reference",
        "model": settings.gmi_image_model,
        "provider": "gmicloud/image",
        "has_api_key": bool(gmi_api_key),
    })
    
    reference_prompt = f"Style reference frame for an explainer video. {spec.style_prompt}"
    logger.info("B0 step queued", extra={
        "stage": "B0.reference",
        "step_index": 0,
        "model": settings.gmi_image_model,
        "provider": "gmicloud/image",
        "prompt": reference_prompt,
    })
    
    gmi_img = get_gmi_image_provider(gmi_api_key)
    return _attach(Pipeline(PIPELINE_NAME, max_concurrency=1)).step(
        gmi_img,
        model=settings.gmi_image_model,
        modality=Modality.IMAGE,
        prompt=reference_prompt,
        aspect_ratio="16:9",
    )


# --- Stage B1: Keyframe images using GMICloud Image Provider --------------

def build_keyframe_pipeline(spec: StoryboardSpec, reference_result, gmi_api_key: str) -> Pipeline:
    """Stage B1 — generate keyframe images for each scene using GMICloud Image Provider."""
    logger.info("build B1 pipeline", extra={
        "stage": "B1.keyframes",
        "model": settings.gmi_image_model,
        "provider": "gmicloud/image",
        "scene_count": len(spec.scenes),
        "has_api_key": bool(gmi_api_key),
        "parent_run_id": getattr(getattr(reference_result, "run", None), "run_id", None),
    })
    
    gmi_img = get_gmi_image_provider(gmi_api_key)
    p = _attach(Pipeline(PIPELINE_NAME, max_concurrency=3))
    
    if reference_result is not None:
        p = p.from_result(reference_result)
    
    style = spec.style_prompt.strip().rstrip(".")
    
    for i, scene in enumerate(spec.scenes):
        prompt = f"{style}. {scene.image_prompt}"
        logger.info("B1 step queued", extra={
            "stage": "B1.keyframes",
            "step_index": i,
            "model": settings.gmi_image_model,
            "provider": "gmicloud/image",
            "caption": scene.caption,
            "prompt": prompt,
        })
        p = p.step(
            gmi_img,
            model=settings.gmi_image_model,
            modality=Modality.IMAGE,
            prompt=prompt,
            aspect_ratio="16:9",
        )
    
    return p


# --- Stage B2: Video + TTS + Music ---------------------------------------

def _resolve_video_provider(gmi_api_key: Optional[str] = None) -> tuple[str, object, str]:
    """Pick the video provider for Stage B2."""
    # Prefer GMICloud if API key provided
    if gmi_api_key:
        logger.info(
            "video provider resolved",
            extra={"provider": "gmicloud", "model": settings.gmi_video_model},
        )
        return (
            "gmicloud",
            GMICloudVideoProvider(api_key=gmi_api_key),
            settings.gmi_video_model,
        )
    
    # Fallback to Decart
    if settings.decart_api_key:
        logger.info(
            "video provider resolved",
            extra={"provider": "decart", "model": settings.decart_video_model},
        )
        return ("decart", DecartVideoProvider(api_key=settings.decart_api_key), settings.decart_video_model)
    
    logger.warning("No video provider configured - Stage B2 video will error")
    return ("decart", DecartVideoProvider(api_key=""), settings.decart_video_model)


def _resolve_tts_provider(elevenlabs_api_key: Optional[str] = None):
    """Pick the TTS provider."""
    # Prefer ElevenLabs if key provided
    if elevenlabs_api_key or settings.elevenlabs_api_key:
        key = elevenlabs_api_key or settings.elevenlabs_api_key
        logger.info("TTS provider resolved", extra={"provider": "elevenlabs", "model": settings.elevenlabs_model})
        return ElevenLabsTTSProvider(api_key=key)
    
    # Fallback to NVIDIA
    if settings.nvidia_api_key:
        logger.info("TTS provider resolved", extra={"provider": "nvidia", "model": settings.tts_model})
        return NvidiaAudioProvider(api_key=settings.nvidia_api_key)
    
    logger.warning("No TTS provider configured - narration will be silent")
    return None


# Kling renders ONLY 5s or 10s clips
_KLING_DURATIONS = (5.0, 10.0)


def snap_scene_durations(spec: StoryboardSpec, gmi_api_key: Optional[str] = None) -> StoryboardSpec:
    """Snap scene durations to the active video provider's supported grid."""
    provider, _, _ = _resolve_video_provider(gmi_api_key)
    if provider != "gmicloud":
        return spec
    
    scenes = [
        s.model_copy(update={
            "duration_sec": min(_KLING_DURATIONS, key=lambda d: abs(d - s.duration_sec)),
        })
        for s in spec.scenes
    ]
    return spec.model_copy(update={
        "scenes": scenes,
        "total_duration_sec": sum(s.duration_sec for s in scenes),
    })


def build_media_pipeline(
    spec: StoryboardSpec, 
    keyframe_result, 
    gmi_api_key: str,
    elevenlabs_api_key: Optional[str] = None
) -> Pipeline:
    """Stage B2 — Generate videos from keyframe images + TTS + music."""
    
    video_label, vid, resolved_video_model = _resolve_video_provider(gmi_api_key)
    tts = _resolve_tts_provider(elevenlabs_api_key)
    
    logger.info("build B2 pipeline", extra={
        "stage": "B2.media",
        "scene_count": len(spec.scenes),
        "video_provider": video_label,
        "video_model": resolved_video_model,
        "tts_provider": "elevenlabs" if (elevenlabs_api_key or settings.elevenlabs_api_key) else "nvidia" if settings.nvidia_api_key else "none",
        "music_model": settings.music_model,
        "has_gmi_key": bool(gmi_api_key),
        "parent_run_id": getattr(keyframe_result.run, "run_id", None),
    })
    
    p = _attach(Pipeline(PIPELINE_NAME, max_concurrency=3, preflight=False))
    p = p.from_result(keyframe_result)
    
    for i, scene in enumerate(spec.scenes):
        # Get the keyframe image from B1
        image_asset = keyframe_result.run.steps[i].assets[0]
        image_ref = presign_asset_url(image_asset.url)
        
        logger.info("B2 scene queued", extra={
            "stage": "B2.media",
            "scene_index": i,
            "video_provider": video_label,
            "video_model": resolved_video_model,
            "motion_prompt": scene.motion_prompt,
            "narration": scene.narration,
            "duration_sec": scene.duration_sec,
            "image_ref_key": backend().key_from_url(image_asset.url),
        })
        
        # Video step - using image-to-video with the keyframe image
        if video_label == "gmicloud":
            video_kwargs = {
                "model": resolved_video_model,
                "modality": Modality.VIDEO,
                "prompt": scene.motion_prompt,
                "duration": scene.duration_sec,
                "external_inputs": [Asset(url=image_ref, media_type="image/png")],
            }
        else:
            video_kwargs = {
                "model": resolved_video_model,
                "modality": Modality.VIDEO,
                "prompt": scene.motion_prompt,
                "duration": scene.duration_sec,
                "image": image_ref,
            }
        
        p = p.step(vid, **video_kwargs)
        
        # TTS step (if available)
        if tts:
            tts_kwargs = {
                "model": settings.elevenlabs_model if (elevenlabs_api_key or settings.elevenlabs_api_key) else settings.tts_model,
                "modality": Modality.AUDIO,
                "prompt": scene.narration,
            }
            if elevenlabs_api_key or settings.elevenlabs_api_key:
                tts_kwargs["voice_id"] = settings.elevenlabs_voice_id
            p = p.step(tts, **tts_kwargs)
        else:
            logger.warning("No TTS provider - narration will be silent", extra={"scene_index": i})
    
    # Music step (if GMI key available)
    if gmi_api_key:
        logger.info("B2 music queued", extra={
            "stage": "B2.media",
            "model": settings.music_model,
            "provider": "gmicloud/audio",
            "prompt": spec.music_prompt,
            "duration_sec": spec.total_duration_sec,
        })
        music = get_gmi_audio_provider(gmi_api_key)
        p = p.step(
            music,
            model=settings.music_model,
            modality=Modality.AUDIO,
            prompt=spec.music_prompt,
            duration=spec.total_duration_sec,
        )
    else:
        logger.warning("No GMI API key - music will be silent")
    
    return p