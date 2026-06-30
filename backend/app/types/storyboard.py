"""Storyboard data types."""

from pydantic import BaseModel, Field, field_validator
from typing import List

class Scene(BaseModel):
    image_prompt: str = Field(..., description="Visual prompt for image generation")
    motion_prompt: str = Field(..., description="Animation/camera movement prompt")
    narration: str = Field(..., description="Spoken narration text")
    caption: str = Field(..., max_length=60, description="Short scene description")
    duration_sec: int = Field(5, ge=3, le=10, description="Scene duration in seconds")

class StoryboardSpec(BaseModel):
    title: str = Field(..., description="Video title")
    style_prompt: str = Field(..., description="Visual style description")
    music_prompt: str = Field(..., description="Background music description")
    scenes: List[Scene] = Field(..., min_length=3, max_length=10)

    @property
    def total_duration_sec(self) -> int:
        return sum(s.duration_sec for s in self.scenes)

    @field_validator('scenes')
    def validate_scene_count(cls, v):
        if len(v) < 3:
            raise ValueError("Need at least 3 scenes")
        if len(v) > 10:
            raise ValueError("Maximum 10 scenes")
        return v