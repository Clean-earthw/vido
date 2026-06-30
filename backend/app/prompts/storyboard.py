"""Google Gemini-optimized storyboard prompts."""

def build_storyboard_prompt(prompt: str, style: str = "cinematic", voice: str = "professional") -> str:
    """Build a storyboard prompt optimized for Gemini."""
    
    style_map = {
        "cinematic": "Cinematic film still, Hollywood blockbuster quality, dramatic lighting, shallow depth of field",
        "anime": "Anime style, Studio Ghibli inspired, vibrant colors, clean lines, beautiful background art",
        "cyberpunk": "Cyberpunk aesthetic, neon lights, rain-slicked streets, high-tech low-life, dark atmosphere",
        "watercolor": "Watercolor painting style, soft edges, flowing colors, artistic brush strokes, ethereal quality",
        "fantasy": "Fantasy art, magical atmosphere, mythical creatures, enchanted forests, glowing elements",
        "noir": "Film noir style, high contrast, dramatic shadows, moody atmosphere, urban setting"
    }
    
    voice_map = {
        "professional": "Speak with a professional, clear, and authoritative tone. Use moderate pace with crisp enunciation.",
        "enthusiastic": "Speak with energetic, excited, and upbeat tone. Use varied pitch and enthusiasm.",
        "calm": "Speak with a soothing, calm, and meditative tone. Use slow, gentle, and warm delivery.",
        "dramatic": "Speak with a theatrical, intense, and dramatic tone. Emphasize key words with varied pacing.",
        "friendly": "Speak with a warm, approachable, and conversational tone. Natural with a smile in your voice."
    }
    
    style_desc = style_map.get(style, style_map["cinematic"])
    voice_desc = voice_map.get(voice, voice_map["professional"])
    
    return f"""You are a professional storyboard artist creating a video in the {style} style.

**STYLE:** {style_desc}
**NARRATOR VOICE:** {voice_desc}

**USER PROMPT:** {prompt}

Create a storyboard with 4-6 scenes that tells a compelling story with a clear beginning, middle, and end.

For each scene, provide:
1. **image_prompt**: A vivid, descriptive prompt for image generation ({style} style, visual details only)
2. **motion_prompt**: A concise prompt describing animation/camera movement
3. **narration**: 1-2 sentences of spoken narration matching the voice style
4. **caption**: A short, descriptive caption under 60 characters
5. **duration_sec**: Either 5 or 10 seconds

Return ONLY valid JSON with this exact structure:
{{
  "title": "catchy and descriptive title",
  "style_prompt": "one-sentence style description for image generation",
  "music_prompt": "mood + genre for background music",
  "scenes": [
    {{
      "image_prompt": "...",
      "motion_prompt": "...",
      "narration": "...",
      "caption": "...",
      "duration_sec": 5
    }}
  ]
}}

Make the story engaging, visually rich, and narratively coherent. Total duration should be 30-60 seconds."""