"""FastAPI application for video generation."""

import asyncio
import json
import logging
import time
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response, StreamingResponse 
from genblaze_core.observability.events import (
    PipelineCompletedEvent,
    PipelineFailedEvent,
    StepCompletedEvent,
)

from app.config import settings
from app.errors import classify
from app.logging_setup import setup_logging, request_id_var, new_request_id
from app.repo.pipelines import (
    generate_storyboard,
    build_reference_pipeline,
    build_keyframe_pipeline,
    build_media_pipeline,
    snap_scene_durations,
    backend,
    sink,
    presign_asset_url,
    probe_storage,
)
from app.repo.composer import compose_final
from app.types.api import GenerateRequest

setup_logging(settings.log_level)
logger = logging.getLogger("api.main")

app = FastAPI(
    title="Vido - AI Video Generator",
    description="One prompt → narrated, scored, captioned MP4. Google Gemini + GMICloud + ElevenLabs TTS.",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https?://localhost(:\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Request logging middleware
@app.middleware("http")
async def request_logging(request: Request, call_next):
    rid = new_request_id()
    token = request_id_var.set(rid)
    start = time.perf_counter()
    
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request failed")
        request_id_var.reset(token)
        raise
    
    duration_ms = int((time.perf_counter() - start) * 1000)
    response.headers["X-Request-Id"] = rid
    logger.info("request", extra={
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": duration_ms
    })
    request_id_var.reset(token)
    return response


# SSE helper
def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, default=str)}\n\n"


# Health check
@app.get("/health")
def health():
    """Health check endpoint."""
    b2_ok = probe_storage()
    return {
        "status": "healthy" if b2_ok else "degraded",
        "b2_connected": b2_ok,
        "providers": {
            "google": bool(settings.google_api_key),
            "gmi": bool(settings.gmi_api_key),
            "elevenlabs": bool(settings.elevenlabs_api_key),
            "nvidia": bool(settings.nvidia_api_key),
            "decart": bool(settings.decart_api_key),
        }
    }


# Storyboard endpoint (Stage A only)
@app.post("/runs/storyboard")
def create_storyboard(req: dict):
    """Stage A only — returns the bare spec for optional client-side refinement."""
    prompt = req.get("prompt", "")
    style = req.get("style", "cinematic")
    voice = req.get("voice", "professional")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    
    try:
        spec, storyboard_key = generate_storyboard(prompt, style, voice)
    except Exception as exc:
        ce = classify(exc)
        raise HTTPException(status_code=ce.status, detail=ce.as_dict()) from exc
    
    return {"spec": spec, "storyboard_key": storyboard_key}


async def _run_pipeline_with_result(pipeline, stage: str, timeout: int = 600, fail_fast: bool = True):
    """Run a pipeline and yield (sse_message, result) tuples."""
    result = None
    
    async for evt in pipeline.astream(
        sink=sink(),
        timeout=timeout,
        fail_fast=fail_fast,
        raise_on_failure=True,
    ):
        sse_msg = _sse({"kind": "stream", "stage": stage, "event": evt.model_dump(mode="json")})
        
        if isinstance(evt, StepCompletedEvent) and evt.step and evt.step.assets:
            asset = evt.step.assets[0]
            asset_msg = _sse({
                "kind": "scene.asset",
                "stage": stage,
                "step_index": evt.step_index,
                "asset_url": asset.url,
                "media_type": asset.media_type,
            })
            yield (sse_msg, None)
            yield (asset_msg, None)
        else:
            if isinstance(evt, (PipelineCompletedEvent, PipelineFailedEvent)) and evt.result is not None:
                result = evt.result
                complete_msg = _sse({"kind": "stage.complete", "stage": stage})
                yield (complete_msg, result)
            else:
                yield (sse_msg, None)
    
    if result is not None:
        yield (None, result)


# Full media generation with SSE streaming
@app.post("/runs/media/stream")
def stream_media(req: GenerateRequest):
    """Stages B0 + B1 + B2 + C as a single SSE stream."""
    
    # Validate Google API key is provided
    if not req.google_api_key or req.google_api_key.strip() == "":
        raise HTTPException(
            status_code=400, 
            detail="Google API key is required. Please provide your Google API key for Gemini."
        )
    
    # Validate GMI API key is provided
    if not req.gmi_api_key or req.gmi_api_key.strip() == "":
        raise HTTPException(
            status_code=400, 
            detail="GMICloud API key is required. Please provide your GMI_API_KEY."
        )
    
    logger.info("media stream endpoint", extra={
        "prompt_chars": len(req.prompt),
        "prompt_preview": req.prompt[:240],
        "style": req.style,
        "voice": req.voice,
        "has_google_key": bool(req.google_api_key),
        "has_gmi_key": bool(req.gmi_api_key),
        "has_elevenlabs_key": bool(req.elevenlabs_api_key),
    })
    
    # Generate storyboard with Gemini using user's Google API key
    spec, _ = generate_storyboard(req.prompt, req.style, req.voice, req.google_api_key)
    spec = snap_scene_durations(spec, req.gmi_api_key)
    
    async def gen():
        current_stage = "B0.reference"
        try:
            # Stage B0 — reference image using user's GMI key
            current_stage = "B0.reference"
            yield _sse({"kind": "stage.start", "stage": current_stage})
            
            b0_result = None
            async for sse_msg, result in _run_pipeline_with_result(
                build_reference_pipeline(spec, req.gmi_api_key),
                current_stage,
                timeout=240
            ):
                if sse_msg:
                    yield sse_msg
                if result is not None:
                    b0_result = result
            
            if b0_result is None:
                yield _sse({"kind": "error", "stage": current_stage, "message": "No pipeline result captured"})
                return
            
            # Stage B1 — keyframes using user's GMI key
            current_stage = "B1.keyframes"
            yield _sse({"kind": "stage.start", "stage": current_stage})
            
            b1_result = None
            async for sse_msg, result in _run_pipeline_with_result(
                build_keyframe_pipeline(spec, b0_result, req.gmi_api_key),
                current_stage,
                timeout=600
            ):
                if sse_msg:
                    yield sse_msg
                if result is not None:
                    b1_result = result
            
            if b1_result is None:
                yield _sse({"kind": "error", "stage": current_stage, "message": "No pipeline result captured"})
                return
            
            # Stage B2 — video + TTS + music using user's keys
            current_stage = "B2.media"
            yield _sse({"kind": "stage.start", "stage": current_stage})
            
            b2_result = None
            async for sse_msg, result in _run_pipeline_with_result(
                build_media_pipeline(spec, b1_result, req.gmi_api_key, req.elevenlabs_api_key),
                current_stage,
                timeout=900,
                fail_fast=False
            ):
                if sse_msg:
                    yield sse_msg
                if result is not None:
                    b2_result = result
            
            if b2_result is None:
                yield _sse({"kind": "error", "stage": current_stage, "message": "No pipeline result captured"})
                return
            
            # Stage C — compose (sync ffmpeg, off the event loop)
            current_stage = "C.compose"
            yield _sse({"kind": "stage.start", "stage": current_stage})
            
            final_asset, notices = await asyncio.to_thread(
                compose_final, b2_result, b1_result, spec
            )
            
            for message in notices:
                yield _sse({"kind": "notice", "stage": "B2.media", "message": message})
            
            manifest_uri = getattr(b2_result.manifest, "manifest_uri", None)
            yield _sse({
                "kind": "compose.complete",
                "asset": final_asset.model_dump(mode="json"),
                "spec": spec.model_dump(mode="json"),
                "run_id": b2_result.run.run_id,
                "manifest_uri": manifest_uri,
            })
            
        except Exception as exc:
            logger.exception("stream_media failed at stage=%s", current_stage)
            ce = classify(exc)
            yield _sse({
                "kind": "error",
                "stage": current_stage,
                "code": ce.code,
                "retryable": ce.retryable,
                "message": ce.message,
                "hint": ce.hint,
            })
    
    return StreamingResponse(gen(), media_type="text/event-stream")


# Asset endpoint
@app.get("/assets/{key:path}")
def get_asset(key: str, inline: bool = False):
    """Serve a B2 object: 302 to a presigned URL, or proxy inline."""
    try:
        if inline:
            return Response(content=backend().get(key), media_type="application/json")
        url = presign_asset_url(key)
    except Exception as exc:
        logger.warning("asset 404", extra={"key": key, "exception": str(exc)})
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    
    return RedirectResponse(url=url, status_code=302)


# List files
@app.get("/files")
def list_files():
    """Enumerate every B2 key under `explainers/`."""
    try:
        page = backend().list("explainers/", max_keys=500)
    except Exception as exc:
        logger.exception("list files failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    
    entries = [
        {
            "key": e.key,
            "size": e.size,
            "last_modified": e.last_modified.isoformat() if e.last_modified else None,
        }
        for e in page.entries
    ]
    return {"prefix": "explainers/", "entries": entries}


@app.get("/runs/{run_id}/assets")
def list_run_assets(run_id: str):
    """Enumerate B2 keys under `explainers/<run_id>/`."""
    prefix = f"explainers/{run_id}/"
    try:
        page = backend().list(prefix, max_keys=200)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    
    entries = [
        {
            "key": e.key,
            "size": e.size,
            "last_modified": e.last_modified.isoformat() if e.last_modified else None,
        }
        for e in page.entries
    ]
    return {"prefix": prefix, "entries": entries}