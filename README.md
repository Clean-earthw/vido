# Vido - AI Video Generation Platform

Vido transforms text prompts into fully produced videos using AI. Simply describe your vision, and watch as our AI pipeline generates a narrated, scored, and captioned video.

## Quick Start

### Prerequisites

**System Requirements:**
- Node.js (v18 or higher)
- Python (v3.10 or higher)
- FFmpeg (latest version)
- Git

**Required Accounts:**
- Backblaze B2 account (free tier available)
- Google Gemini API key
- GMICloud API key (user-provided during generation)
- ElevenLabs API key (optional, can use server default)

### Installation & Setup

**1. Clone the repository**

```bash
git clone https://github.com/Clean-earthw/vido.git
cd storyforge
```

**2. Frontend Setup**

```bash
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:3000`

**3. Backend Setup**

```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

**4. Configure Environment**

Create a `.env` file in the backend directory:

```env
# Backblaze B2 (Required)
B2_REGION=us-east-005
B2_KEY_ID=your_b2_key_id
B2_APPLICATION_KEY=your_b2_app_key
B2_BUCKET_NAME=your_bucket_name

# Google Gemini (Required)
GOOGLE_API_KEY=your_google_api_key

# ElevenLabs (Optional - server fallback)
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb

# API Configuration
API_CORS_ORIGINS=http://localhost:3000,http://localhost:3001
LOG_LEVEL=INFO
```

**5. Run the Backend**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**6. Access the Application**

- Open `http://localhost:3000` in your browser
- Enter your GMICloud API key
- Describe your video idea
- Click "Generate Video"

## How It Works

StoryForge uses a multi-stage AI pipeline:

1. **Storyboard**: Google Gemini analyzes your prompt and creates a structured scene plan
2. **Visuals**: GMICloud generates cinematic keyframe images
3. **Animation**: Kling technology converts images to motion video clips
4. **Audio**: ElevenLabs adds narration, GMICloud adds background music
5. **Composition**: FFmpeg assembles all elements into a final MP4

## Technologies

**Backend**: FastAPI, Python, Genblaze Framework, FFmpeg
**Frontend**: Next.js, TypeScript, Tailwind CSS, Framer Motion
**Storage**: Backblaze B2
**AI Providers**: Google Gemini, GMICloud, ElevenLabs

## Troubleshooting

**FFmpeg not found**: Ensure FFmpeg is installed and in your PATH
**API key errors**: Verify your Backblaze and Google Gemini keys are correct
**CORS issues**: Check `API_CORS_ORIGINS` includes your frontend URL
