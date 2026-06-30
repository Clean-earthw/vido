"""API request/response types for the video generation service."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


class VideoStyle(str, Enum):
    """Available visual styles for video generation."""
    CINEMATIC = "cinematic"
    ANIME = "anime"
    CYBERPUNK = "cyberpunk"
    WATERCOLOR = "watercolor"
    FANTASY = "fantasy"
    NOIR = "noir"


class VoicePersonality(str, Enum):
    """Available voice personalities for narration."""
    PROFESSIONAL = "professional"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"
    DRAMATIC = "dramatic"
    FRIENDLY = "friendly"


class VideoLength(str, Enum):
    """Video length options."""
    SHORT = "short"      # 15-30s
    MEDIUM = "medium"    # 30-60s
    LONG = "long"        # 60-90s

class GenerateRequest(BaseModel):
    prompt: str
    style: str = "cinematic"
    voice: str = "professional"
    google_api_key: str  # Required - user must provide their Google API key for Gemini
    gmi_api_key: str  # Required - user must provide their GMI API key
    elevenlabs_api_key: Optional[str] = None  # Optional - uses default if not provided



    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate and clean the prompt."""
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()

    @field_validator('style')
    @classmethod
    def validate_style(cls, v: VideoStyle) -> VideoStyle:
        """Validate style is supported."""
        if v not in VideoStyle:
            raise ValueError(f"Unsupported style: {v}")
        return v

    @field_validator('voice')
    @classmethod
    def validate_voice(cls, v: VoicePersonality) -> VoicePersonality:
        """Validate voice is supported."""
        if v not in VoicePersonality:
            raise ValueError(f"Unsupported voice: {v}")
        return v


class GenerateResponse(BaseModel):
    """Response model for successful video generation."""
    
    video_url: str = Field(..., description="URL of the generated video")
    manifest_url: str = Field(..., description="URL of the provenance manifest")
    title: str = Field(..., description="Video title")
    duration: int = Field(..., description="Video duration in seconds", ge=1)
    scenes: int = Field(..., description="Number of scenes", ge=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "video_url": "https://b2.example.com/explainers/abc123/final.mp4",
                "manifest_url": "https://b2.example.com/explainers/abc123/manifest.json",
                "title": "The Future of AI",
                "duration": 45,
                "scenes": 5
            }
        }
    }


class StoryboardRequest(BaseModel):
    """Request model for storyboard generation only."""
    
    prompt: str = Field(
        ...,
        description="User's video idea description",
        min_length=10,
        max_length=1000
    )
    style: VideoStyle = Field(
        default=VideoStyle.CINEMATIC,
        description="Visual style for the video"
    )
    voice: VoicePersonality = Field(
        default=VoicePersonality.PROFESSIONAL,
        description="Voice personality for narration"
    )
    length: VideoLength = Field(
        default=VideoLength.MEDIUM,
        description="Target video length"
    )

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class StoryboardResponse(BaseModel):
    """Response model for storyboard generation."""
    
    spec: dict = Field(..., description="Storyboard specification")
    storyboard_key: str = Field(..., description="B2 storage key for the storyboard")


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status: healthy or degraded")
    b2_connected: bool = Field(..., description="Whether B2 storage is accessible")
    providers: dict = Field(..., description="Provider availability status")
    ffmpeg_present: bool = Field(default=False, description="Whether ffmpeg is available")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "b2_connected": True,
                "providers": {
                    "google": True,
                    "gmi": True,
                    "nvidia": True,
                    "elevenlabs": False,
                    "decart": False
                },
                "ffmpeg_present": True
            }
        }
    }


class ErrorResponse(BaseModel):
    """Error response model."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="User-friendly error message")
    hint: Optional[str] = Field(None, description="Suggestion for resolution")
    retryable: bool = Field(default=True, description="Whether the error is retryable")

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "RATE_LIMIT",
                "message": "Rate limit exceeded. Please wait and try again.",
                "hint": "The AI service is experiencing high demand. Try again in a few minutes.",
                "retryable": True
            }
        }
    }


class FileMetadata(BaseModel):
    """File metadata from B2 storage."""
    
    key: str = Field(..., description="Object key in B2")
    size: int = Field(..., description="File size in bytes")
    last_modified: Optional[str] = Field(None, description="ISO timestamp of last modification")
    run_id: Optional[str] = Field(None, description="Run ID derived from the key")
    display_name: Optional[str] = Field(None, description="User-friendly file name")


class FilesResponse(BaseModel):
    """Response model for file listing."""
    
    prefix: str = Field(..., description="Storage prefix")
    entries: List[FileMetadata] = Field(default_factory=list, description="List of files")


class RunAssetsResponse(BaseModel):
    """Response model for run assets listing."""
    
    prefix: str = Field(..., description="Run-specific prefix")
    entries: List[FileMetadata] = Field(default_factory=list, description="List of assets in the run")