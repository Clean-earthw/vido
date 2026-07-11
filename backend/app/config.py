"""Centralised settings with Google + GMICloud configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"

class Settings(BaseSettings):
    # --- Backblaze B2 ---
    b2_region: str = "us-east-005"
    b2_key_id: str = ""
    b2_application_key: str = ""
    b2_bucket_name: str = ""

    # --- Google AI (Gemini for storyboard) ---
    google_api_key: str = ""
    google_project_id: Optional[str] = None
    google_location: str = "us-central1"

    # --- Gemini Chat (Storyboard generation) ---
    chat_model: str = "gemini-2.5-flash"
    chat_temperature: float = 0.7

    # --- Veo Video Generation ---
    video_model: str = "veo-3.0-generate-001"  # veo-3.0-generate-001, veo-3.0-fast-generate-001, veo-2.0-generate-001
    veo_resolution: str = "720p"  # 720p or 1080p

    # --- GMICloud (Image + Video Generation) ---
    gmi_api_key: str = "" # User will provide this
    gmi_image_model: str = "seedream-5.0-lite"  # Text-to-image model
    gmi_video_model: str = "Kling-Image2Video-V2.1-Master"

    # --- ElevenLabs TTS (Primary) ---
    elevenlabs_api_key: str = "sk_b421769fe8ad92970bba32f0f300a1221e609e8006fbe520"
    elevenlabs_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"
    elevenlabs_model: str = "eleven_v3"

    # --- NVIDIA TTS (Fallback) ---
    nvidia_api_key: str = ""
    tts_model: str = "nvidia/magpie-tts-multilingual"

    # --- GMICloud Audio (Music) ---
    music_model: str = "minimax-music-2.5"

    # --- Decart (Fallback video) ---
    decart_api_key: str = ""
    video_model: str = "lucy-2.1"

    # --- Observability ---
    otel_endpoint: str = ""
    step_cache_dir: str = "./.cache/explainers"
    log_level: str = "INFO"

    # --- API ---
    api_cors_origins: str = "http://localhost:3000,http://localhost:3001"

    model_config = {"env_file": str(_ROOT_ENV), "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]

settings = Settings()