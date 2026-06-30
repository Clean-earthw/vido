"use client";

import { ImageIcon, Film, Loader2 } from "lucide-react";

interface ScenePreviewProps {
  scene: {
    index: number;
    caption?: string;
    image_url?: string;
    video_url?: string;
  };
  index: number;
}

export function ScenePreview({ scene, index }: ScenePreviewProps) {
  const hasImage = !!scene.image_url;
  const hasVideo = !!scene.video_url;
  const isComplete = hasImage || hasVideo;

  return (
    <div className="bg-white border-2 border-gray-300 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition">
      <div className="aspect-video bg-gray-100 relative flex items-center justify-center">
        {hasVideo ? (
          <video
            src={scene.video_url}
            className="w-full h-full object-cover"
            muted
            loop
            playsInline
          />
        ) : hasImage ? (
          <img
            src={scene.image_url}
            alt={`Scene ${index + 1}`}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center gap-2 text-gray-400">
            <Loader2 className="w-8 h-8 animate-spin" />
            <span className="text-xs">Generating...</span>
          </div>
        )}
        
        {/* Badge */}
        <div className="absolute top-2 left-2 bg-black/70 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-lg">
          Scene {index + 1}
        </div>
        
        {isComplete && (
          <div className="absolute bottom-2 right-2 bg-black/70 backdrop-blur-sm rounded-lg p-1">
            {hasVideo ? (
              <Film className="w-3 h-3 text-white" />
            ) : (
              <ImageIcon className="w-3 h-3 text-white" />
            )}
          </div>
        )}
      </div>
      {scene.caption && (
        <div className="p-2 text-xs text-gray-600 truncate text-center border-t border-gray-100">
          {scene.caption}
        </div>
      )}
    </div>
  );
}