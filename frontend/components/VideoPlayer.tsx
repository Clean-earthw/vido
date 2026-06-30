"use client";

import { useState, useRef } from "react";
import { Play, Pause, Volume2, VolumeX, Maximize } from "lucide-react";

interface VideoPlayerProps {
  url: string;
  title?: string;
}

export function VideoPlayer({ url, title }: VideoPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const toggleFullscreen = () => {
    if (videoRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        videoRef.current.requestFullscreen();
      }
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const progress = (videoRef.current.currentTime / videoRef.current.duration) * 100;
      setProgress(progress);
    }
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    if (videoRef.current) {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      videoRef.current.currentTime = x * videoRef.current.duration;
    }
  };

  return (
    <div className="relative bg-black rounded-xl overflow-hidden">
      <video
        ref={videoRef}
        src={url}
        className="w-full aspect-video"
        onTimeUpdate={handleTimeUpdate}
        onClick={togglePlay}
        playsInline
      />
      
      {/* Controls Overlay */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
        {/* Progress Bar */}
        <div
          className="w-full h-1 bg-white/30 rounded-full cursor-pointer mb-3"
          onClick={handleSeek}
        >
          <div
            className="h-full bg-blue-500 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="text-white hover:text-blue-400 transition"
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </button>
            <button
              onClick={toggleMute}
              className="text-white hover:text-blue-400 transition"
            >
              {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
            </button>
            {title && (
              <span className="text-white text-sm font-medium truncate max-w-[200px]">
                {title}
              </span>
            )}
          </div>
          <button
            onClick={toggleFullscreen}
            className="text-white hover:text-blue-400 transition"
          >
            <Maximize className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}