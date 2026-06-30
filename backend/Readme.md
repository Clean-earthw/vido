# Backend Documentation

## Overview

The backend is a FastAPI-based video generation service that orchestrates multiple AI providers to transform text prompts into fully produced videos. It follows a pipeline architecture with four main stages:

1. **Storyboard Generation** (Google Gemini)
2. **Image Generation** (GMICloud)
3. **Video Generation** (GMICloud)
4. **Audio & Composition** (ElevenLabs/NVIDIA + GMICloud)

## Architecture

### Pipeline Stages

#### Stage A: Storyboard Planning
- **Provider**: Google Gemini (via `genblaze_google`)
- **Model**: `gemini-2.5-pro`
- **Purpose**: Generates a structured storyboard from a text prompt
- **Output**: JSON specification containing:
  - Title
  - Style prompt
  - Music prompt
  - Scene list with image prompts, motion prompts, narration, and durations

#### Stage B0: Reference Image
- **Provider**: GMICloud Image Provider (`genblaze_gmicloud.GMICloudImageProvider`)
- **Model**: `seedream-5.0-lite`
- **Purpose**: Generates a style reference image
- **Output**: Single image (16:9 aspect ratio)

#### Stage B1: Keyframe Images
- **Provider**: GMICloud Image Provider
- **Model**: `seedream-5.0-lite`
- **Purpose**: Generates keyframe images for each scene
- **Output**: Multiple images (16:9 aspect ratio)

#### Stage B2: Video + Audio
- **Video Provider**: GMICloud Video Provider (`GMICloudVideoProvider`)
- **Video Model**: `Kling-Image2Video-V2.1-Master`
- **TTS Provider**: ElevenLabs (`ElevenLabsTTSProvider`) with NVIDIA as fallback
- **TTS Model**: `eleven_v3` (or `nvidia/magpie-tts-multilingual`)
- **Audio Provider**: GMICloud Audio Provider (`GMICloudAudioProvider`)
- **Audio Model**: `minimax-music-2.5`
- **Purpose**: 
  - Converts keyframe images to videos with motion
  - Adds voiceover narration
  - Generates background music

#### Stage C: Composition
- **Tool**: FFmpeg (via `compose_final`)
- **Purpose**: 
  - Merges all video clips
  - Syncs audio tracks
  - Adds captions
  - Produces final MP4

## Provider & Model Details

### Google Gemini
- **Purpose**: Storyboard generation
- **Model**: `gemini-2.5-pro`
- **API Key**: Provided via `GOOGLE_API_KEY` environment variable
- **Note**: Uses `genblaze_google.chat()` for chat completion

### GMICloud
- **Purpose**: Image generation, video generation, music generation
- **Models**:
  - Image: `seedream-5.0-lite` (text-to-image)
  - Video: `Kling-Image2Video-V2.1-Master` (image-to-video)
  - Music: `minimax-music-2.5`
- **API Key**: User-provided via frontend
- **Note**: 
  - Image generation uses `GMICloudImageProvider`
  - Video generation uses `GMICloudVideoProvider` with `external_inputs`
  - Music generation uses `GMICloudAudioProvider`

### ElevenLabs
- **Purpose**: Text-to-Speech for narration
- **Model**: `eleven_v3`
- **Voice ID**: Configurable via settings
- **API Key**: User-provided (optional, falls back to server key)
- **Note**: Primary TTS provider

### NVIDIA (Fallback)
- **Purpose**: Text-to-Speech fallback
- **Model**: `nvidia/magpie-tts-multilingual`
- **API Key**: Server-configured
- **Note**: Used only when ElevenLabs is unavailable

### Backblaze B2
- **Purpose**: Cloud storage for all generated assets
- **Bucket**: `denisbucket`
- **Region**: `us-east-005`
- **Features**: 
  - Automatic presigned URLs
  - Hierarchical key structure (`explainers/<run-id>/`)
  - Asset lifecycle management

### Decart (Fallback Video)
- **Purpose**: Video generation fallback
- **Model**: `lucy-2.1`
- **API Key**: Server-configured
- **Note**: Used only when GMICloud is unavailable

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings & configuration
│   ├── logging_setup.py     # Logging configuration
│   ├── errors.py            # Error classification
│   ├── repo/
│   │   ├── pipelines.py     # Pipeline definitions
│   │   ├── composer.py      # FFmpeg composition
│   │   └── __init__.py
│   ├── types/
│   │   ├── api.py           # API request/response types
│   │   ├── storyboard.py    # Storyboard spec types
│   │   └── __init__.py
│   ├── prompts/
│   │   └── storyboard.py    # Storyboard prompt templates
│   └── __init__.py
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
└── README.md                 # This file
```

## API Endpoints

### Health Check
```
GET /health
```
Returns service health and provider availability.

### Storyboard Generation
```
POST /runs/storyboard
```
Generates a storyboard spec without full video generation.

**Request Body**:
```json
{
  "prompt": "A futuristic city...",
  "style": "cinematic",
  "voice": "professional"
}
```

### Full Media Generation (SSE Stream)
```
POST /runs/media/stream
```
Generates complete video with SSE progress streaming.

**Request Body**:
```json
{
  "prompt": "A futuristic city...",
  "style": "cinematic",
  "voice": "professional",
  "gmi_api_key": "eyJhbGc...",
  "elevenlabs_api_key": "sk_..."  // Optional
}
```

**SSE Events**:
- `stage.start` - Stage begins
- `stage.complete` - Stage completes
- `scene.asset` - New asset generated (image/video)
- `compose.complete` - Final video ready
- `error` - Error occurred
- `notice` - Warning/notice message

### Asset Access
```
GET /assets/{key:path}
```
Returns a presigned URL for an asset.

### File Listing
```
GET /files
```
Lists all assets in the storage bucket.

```
GET /runs/{run_id}/assets
```
Lists assets for a specific run.

## Installation

### Prerequisites

- Python 3.10+
- FFmpeg (for video composition)
- Backblaze B2 account (for storage)
- GMICloud API key (user-provided)
- Google Gemini API key
- ElevenLabs API key (optional)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install FFmpeg:
```bash
# On Ubuntu/Debian:
sudo apt-get install ffmpeg

# On macOS:
brew install ffmpeg

# On Windows:
# Download from https://ffmpeg.org/download.html
# Add to PATH
```

5. Create `.env` file in the backend directory:
```env
# Backblaze B2
B2_REGION=us-east-005
B2_KEY_ID=your_key_id
B2_APPLICATION_KEY=your_application_key
B2_BUCKET_NAME=your_bucket_name

# Google Gemini
GOOGLE_API_KEY=your_google_api_key

# Optional server-side defaults
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb

# NVIDIA TTS (fallback)
NVIDIA_API_KEY=your_nvidia_key

# Decart (fallback video)
DECART_API_KEY=your_decart_key

# Observability (optional)
OTEL_ENDPOINT=your_otel_endpoint
LOG_LEVEL=INFO

# API
API_CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Running the Application

### Development Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Python directly
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `B2_REGION` | Yes | Backblaze B2 region |
| `B2_KEY_ID` | Yes | Backblaze B2 key ID |
| `B2_APPLICATION_KEY` | Yes | Backblaze B2 application key |
| `B2_BUCKET_NAME` | Yes | Backblaze B2 bucket name |
| `GOOGLE_API_KEY` | Yes | Google Gemini API key |
| `ELEVENLABS_API_KEY` | No | ElevenLabs TTS API key (server fallback) |
| `ELEVENLABS_VOICE_ID` | No | ElevenLabs voice ID |
| `NVIDIA_API_KEY` | No | NVIDIA TTS API key (fallback) |
| `DECART_API_KEY` | No | Decart video API key (fallback) |
| `OTEL_ENDPOINT` | No | OpenTelemetry endpoint |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `API_CORS_ORIGINS` | No | CORS allowed origins |

## Key Features

### API Key Management
- GMICloud API key is **required** from the user
- ElevenLabs API key is **optional** (uses server key if not provided)
- Keys are passed per-request and never stored on the server
- All keys are transmitted securely via HTTPS

### SSE Streaming
- Real-time progress updates
- Asset previews as they're generated
- Detailed error messages
- Non-blocking generation

### Storage & Asset Management
- All assets stored in Backblaze B2
- Hierarchical organization by run ID
- Automatic presigned URLs for secure access
- Asset verification with SHA256 hashes

### Error Handling
- Classified error responses
- Retryable error detection
- Detailed error messages with hints
- Graceful fallbacks for providers

## Dependencies

### Core Dependencies
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `pydantic-settings` - Settings management

### Genblaze Providers
- `genblaze-gmicloud` - GMICloud integration
- `genblaze-google` - Google Gemini + Imagen integration
- `genblaze-elevenlabs` - ElevenLabs TTS integration
- `genblaze-nvidia` - NVIDIA TTS integration
- `genblaze-decarte` - Decart video integration
- `genblaze-s3` - S3/Backblaze B2 integration
- `genblaze-core` - Core pipeline functionality

### Utilities
- `python-multipart` - Form data parsing
- `python-dotenv` - Environment variables

## Example Usage

### Frontend Integration

```typescript
const response = await fetch("http://localhost:8000/runs/media/stream", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    prompt: "A futuristic city where AI helps humans",
    style: "cinematic",
    voice: "professional",
    gmi_api_key: "eyJhbGc...",
    elevenlabs_api_key: "sk_..." // Optional
  })
});

// Stream SSE events
const reader = response.body.getReader();
// ... process SSE events
```

### cURL Example

```bash
curl -X POST http://localhost:8000/runs/media/stream \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A futuristic city where AI helps humans",
    "style": "cinematic",
    "voice": "professional",
    "gmi_api_key": "eyJhbGc..."
  }'
```

## Troubleshooting

### Common Issues

1. **"GMICloud API key is required"**
   - Ensure user provides a valid GMI API key
   - Check key format and permissions

2. **"modality 'image' not supported"**
   - Ensure using correct provider for modality
   - `GMICloudImageProvider` for images
   - `GMICloudVideoProvider` for videos

3. **"Unsafe chain input URL"**
   - Use HTTPS URLs for external inputs
   - Avoid data: URLs or file:// paths

4. **FFmpeg not found**
   - Install FFmpeg and ensure it's in PATH
   - Check `ffmpeg` command works in terminal

### Logging

Logs are written with request IDs for traceability:
```
{"timestamp": "2026-06-30 02:27:18,930", "level": "INFO", "request_id": "1b037772", "name": "api.main", "message": "media stream endpoint", "extra": {...}}
```

## License

MIT

## Support

For issues and questions, please open an issue in the repository.