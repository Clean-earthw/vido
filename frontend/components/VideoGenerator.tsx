"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Sparkles, 
  Film, 
  Loader2, 
  AlertCircle,
  Download,
  Share2,
  RefreshCw,
  Zap,
  Wand2,
  Key,
  Eye,
  EyeOff,
  X
} from "lucide-react";
import { StyleSelector } from "@/components/StyleSelector";
import { VoiceSelector } from "@/components/VoiceSelector";
import { ScenePreview } from "@/components/ScenePreview";
import { ProgressBar } from "@/components/ProgressBar";
import { VideoPlayer } from "@/components/VideoPlayer";
import { useVideoGeneration } from "@/hooks/useVideoGeneration";
import { VideoStyle, formatDuration } from "@/lib/api-client";

// Type guard for VideoStyle
const isValidVideoStyle = (value: string): value is VideoStyle => {
  const validStyles: VideoStyle[] = ["cinematic", "anime", "cyberpunk", "watercolor", "fantasy", "noir"];
  return validStyles.includes(value as VideoStyle);
};

export default function VideoGenerator() {
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState<VideoStyle>("cinematic");
  const [voice, setVoice] = useState("professional");
  const [googleApiKey, setGoogleApiKey] = useState("");
  const [gmiApiKey, setGmiApiKey] = useState("");
  const [elevenlabsApiKey, setElevenlabsApiKey] = useState("");
  const [showGoogleKey, setShowGoogleKey] = useState(false);
  const [showGmiKey, setShowGmiKey] = useState(false);
  const [showElevenlabsKey, setShowElevenlabsKey] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  
  const { generate, reset, status, progress, scenes, videoUrl, error, videoTitle, videoDuration } = useVideoGeneration();

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    if (!googleApiKey.trim()) {
      alert("Please enter your Google API key");
      return;
    }
    if (!gmiApiKey.trim()) {
      alert("Please enter your GMICloud API key");
      return;
    }
    setShowProgressModal(true);
    await generate({ 
      prompt, 
      style: style as VideoStyle,
      voice, 
      google_api_key: googleApiKey,
      gmi_api_key: gmiApiKey,
      elevenlabs_api_key: elevenlabsApiKey || undefined
    });
  };

  const handleStyleChange = (value: string) => {
    if (isValidVideoStyle(value)) {
      setStyle(value);
    } else {
      console.warn(`Invalid style value: ${value}`);
      setStyle("cinematic");
    }
  };

  const handleCloseModal = () => {
    if (status === "generating") {
      if (confirm("Generation in progress. Are you sure you want to close?")) {
        setShowProgressModal(false);
        reset();
      }
    } else {
      setShowProgressModal(false);
    }
  };

  const isGenerating = status === "generating";
  const isComplete = status === "complete";
  const hasError = status === "error";
  const isIdle = status === "idle";

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && prompt.trim() && googleApiKey.trim() && gmiApiKey.trim()) {
      e.preventDefault();
      handleGenerate();
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        {/* Header */}
        <motion.header 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10 md:mb-14"
        >
          <div className="flex items-center justify-center gap-4 mb-4">
            <div className="p-3 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl shadow-lg shadow-blue-500/30">
              <Film className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
              Vido
            </h1>
          </div>
          <p className="text-gray-600 text-base md:text-lg flex items-center justify-center gap-2">
            <Zap className="w-4 h-4 text-amber-500" />
            Transform your ideas into professional AI-generated videos
          </p>
          <div className="mt-3 flex items-center justify-center gap-2 text-sm text-gray-500">
            <span className="inline-flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
              Powered by AI
            </span>
            <span className="w-px h-4 bg-gray-300"></span>
            <span>Google Gemini · GMICloud · ElevenLabs</span>
          </div>
        </motion.header>

        {/* Main Card */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 md:p-8 mb-8 shadow-xl shadow-gray-200/50 border border-gray-200/50"
        >
          <div className="space-y-6">
            {/* API Key Inputs */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-gray-700 text-sm font-semibold mb-2">
                  <span className="flex items-center gap-2">
                    <Key className="w-4 h-4 text-gray-500" />
                    Google API Key <span className="text-red-500">*</span>
                  </span>
                </label>
                <div className="relative">
                  <input
                    type={showGoogleKey ? "text" : "password"}
                    value={googleApiKey}
                    onChange={(e) => setGoogleApiKey(e.target.value)}
                    placeholder="Enter your Google API key"
                    className="w-full bg-white text-gray-800 rounded-xl px-4 py-3 border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all pr-10 placeholder:text-gray-400"
                    disabled={isGenerating}
                  />
                  <button
                    type="button"
                    onClick={() => setShowGoogleKey(!showGoogleKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition"
                  >
                    {showGoogleKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1.5">
                  Required for Gemini storyboard generation
                </p>
              </div>

              <div>
                <label className="block text-gray-700 text-sm font-semibold mb-2">
                  <span className="flex items-center gap-2">
                    <Key className="w-4 h-4 text-gray-500" />
                    GMICloud API Key <span className="text-red-500">*</span>
                  </span>
                </label>
                <div className="relative">
                  <input
                    type={showGmiKey ? "text" : "password"}
                    value={gmiApiKey}
                    onChange={(e) => setGmiApiKey(e.target.value)}
                    placeholder="Enter your GMI_API_KEY"
                    className="w-full bg-white text-gray-800 rounded-xl px-4 py-3 border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all pr-10 placeholder:text-gray-400"
                    disabled={isGenerating}
                  />
                  <button
                    type="button"
                    onClick={() => setShowGmiKey(!showGmiKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition"
                  >
                    {showGmiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1.5">
                  Required for image, video, and music generation
                </p>
              </div>
            </div>

            {/* ElevenLabs API Key (Optional) */}
            <div>
              <label className="block text-gray-700 text-sm font-semibold mb-2">
                <span className="flex items-center gap-2">
                  <Key className="w-4 h-4 text-gray-500" />
                  ElevenLabs API Key <span className="text-gray-400 font-normal">(optional)</span>
                </span>
              </label>
              <div className="relative">
                <input
                  type={showElevenlabsKey ? "text" : "password"}
                  value={elevenlabsApiKey}
                  onChange={(e) => setElevenlabsApiKey(e.target.value)}
                  placeholder="Enter your ElevenLabs API key (optional)"
                  className="w-full bg-white text-gray-800 rounded-xl px-4 py-3 border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all pr-10 placeholder:text-gray-400"
                  disabled={isGenerating}
                />
                <button
                  type="button"
                  onClick={() => setShowElevenlabsKey(!showElevenlabsKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition"
                >
                  {showElevenlabsKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1.5">
                Uses default ElevenLabs key if not provided
              </p>
            </div>

            {/* Prompt Input */}
            <div>
              <label className="block text-gray-700 text-sm font-semibold mb-2">
                What story do you want to tell?
              </label>
              <div className="relative">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Describe your vision... e.g., 'A futuristic city where humans and AI work together to solve climate change...'"
                  className="w-full h-28 md:h-32 bg-white text-gray-800 rounded-xl p-4 border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all resize-none placeholder:text-gray-400"
                  disabled={isGenerating}
                  maxLength={1000}
                />
                <div className="absolute bottom-3 right-3 text-xs text-gray-400">
                  {prompt.length}/1000
                </div>
              </div>
            </div>

            {/* Selectors */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <StyleSelector 
                value={style} 
                onChange={handleStyleChange} 
                disabled={isGenerating} 
              />
              <VoiceSelector value={voice} onChange={setVoice} disabled={isGenerating} />
            </div>

            {/* Generate Button */}
            <motion.button
              whileHover={!isGenerating ? { scale: 1.01 } : {}}
              whileTap={!isGenerating ? { scale: 0.99 } : {}}
              onClick={handleGenerate}
              disabled={!prompt.trim() || !googleApiKey.trim() || !gmiApiKey.trim() || isGenerating}
              className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold rounded-xl shadow-lg shadow-blue-500/25 hover:shadow-blue-500/35 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-blue-500/25 flex items-center justify-center gap-2.5 text-lg"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generating your video...
                </>
              ) : isComplete ? (
                <>
                  <RefreshCw className="w-5 h-5" />
                  Create Another Video
                </>
              ) : (
                <>
                  <Wand2 className="w-5 h-5" />
                  Generate Video
                </>
              )}
            </motion.button>
          </div>
        </motion.div>

        {/* Progress Modal */}
        <AnimatePresence>
          {showProgressModal && (isGenerating || isComplete || hasError) && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={handleCloseModal}
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="bg-white rounded-2xl p-6 md:p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              >
                {/* Modal Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl">
                      <Film className="w-5 h-5 text-white" />
                    </div>
                    <h2 className="text-xl font-bold text-gray-800">
                      {isGenerating ? "Generating Your Video" : isComplete ? "Video Ready!" : "Generation Failed"}
                    </h2>
                  </div>
                  <button
                    onClick={handleCloseModal}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500 hover:text-gray-700"
                    disabled={isGenerating}
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Progress Bar */}
                <div className="mb-6">
                  <ProgressBar progress={progress} />
                </div>

                {/* Scenes Preview in Modal */}
                {scenes.length > 0 && (
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-amber-500" />
                        Storyboard
                        <span className="text-xs text-gray-400 font-normal ml-1">
                          ({scenes.length} scenes)
                        </span>
                      </h3>
                      {videoDuration > 0 && (
                        <span className="text-xs text-gray-400">
                          ⏱️ {formatDuration(videoDuration)}
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {scenes.map((scene, index) => (
                        <ScenePreview key={index} scene={scene} index={index} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Error Display */}
                {hasError && error && (
                  <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <h3 className="text-red-700 font-medium">Generation Failed</h3>
                      <p className="text-red-600 text-sm">{error}</p>
                      <button 
                        onClick={() => {
                          reset();
                          setShowProgressModal(false);
                        }}
                        className="text-red-600 text-sm font-medium hover:text-red-700 transition-colors mt-1"
                      >
                        Try again
                      </button>
                    </div>
                  </div>
                )}

                {/* Video Player in Modal */}
                {isComplete && videoUrl && (
                  <div className="space-y-4">
                    {videoTitle && (
                      <h3 className="text-lg font-semibold text-gray-800 text-center">
                        {videoTitle}
                      </h3>
                    )}
                    
                    <VideoPlayer url={videoUrl} title={videoTitle || undefined} />
                    
                    <div className="flex flex-wrap gap-3 justify-center pt-2">
                      <button
                        onClick={() => {
                          const a = document.createElement("a");
                          a.href = videoUrl;
                          a.download = `${videoTitle || "video"}.mp4`;
                          a.click();
                        }}
                        className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition-colors flex items-center gap-2 shadow-lg shadow-blue-500/25"
                      >
                        <Download className="w-4 h-4" />
                        Download Video
                      </button>
                      
                      <button
                        onClick={async () => {
                          if (navigator.share) {
                            try {
                              await navigator.share({
                                title: videoTitle || "My AI-generated video",
                                text: `Check out my AI-generated video: ${videoTitle || ""}`,
                                url: videoUrl,
                              });
                            } catch {
                              // User cancelled
                            }
                          } else {
                            await navigator.clipboard.writeText(videoUrl);
                            alert("Video link copied to clipboard!");
                          }
                        }}
                        className="px-5 py-2.5 bg-gray-600 hover:bg-gray-700 rounded-lg text-white font-medium transition-colors flex items-center gap-2"
                      >
                        <Share2 className="w-4 h-4" />
                        Share
                      </button>

                      <button
                        onClick={() => {
                          setShowProgressModal(false);
                          reset();
                        }}
                        className="px-5 py-2.5 bg-gray-200 hover:bg-gray-300 rounded-lg text-gray-700 font-medium transition-colors flex items-center gap-2"
                      >
                        <RefreshCw className="w-4 h-4" />
                        Create Another
                      </button>
                    </div>
                  </div>
                )}

                {/* Generating Status */}
                {isGenerating && (
                  <div className="text-center py-4">
                    <p className="text-gray-600 text-sm">
                      This may take a few minutes. Please wait...
                    </p>
                    <div className="mt-3 flex justify-center gap-1.5">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                )}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer */}
        {isIdle && !scenes.length && (
          <motion.footer
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-center text-gray-500 text-sm mt-16 pt-8 border-t border-gray-200"
          >
            <p className="font-medium">Powered by Google Gemini · GMICloud · ElevenLabs TTS</p>
            <p className="text-xs mt-2 text-gray-400">
              Enter your API keys to start creating professional videos
            </p>
          </motion.footer>
        )}
      </div>
    </main>
  );
}