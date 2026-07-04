"use client";

import { useState, useCallback, useRef } from "react";
import {
  streamMediaGeneration,
  SceneAssetEvent,
  ComposeCompleteEvent,
  ErrorEvent,
  NoticeEvent,
  VideoStyle,
} from "@/lib/api-client";

interface Scene {
  index: number;
  caption?: string;
  image_url?: string;
  video_url?: string;
  duration?: number;
}

interface GenerateParams {
  prompt: string;
  style: VideoStyle;
  voice: string;
  google_api_key: string;
  gmi_api_key: string;
  elevenlabs_api_key?: string;
}

interface UseVideoGenerationReturn {
  generate: (params: GenerateParams) => Promise<void>;
  reset: () => void;
  status: "idle" | "generating" | "complete" | "error";
  progress: number;
  scenes: Scene[];
  videoUrl: string | null;
  videoTitle: string | null;
  videoDuration: number;
  error: string | null;
}

export function useVideoGeneration(): UseVideoGenerationReturn {
  const [status, setStatus] = useState<"idle" | "generating" | "complete" | "error">("idle");
  const [progress, setProgress] = useState(0);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [videoTitle, setVideoTitle] = useState<string | null>(null);
  const [videoDuration, setVideoDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);
  
  const abortControllerRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStatus("idle");
    setProgress(0);
    setScenes([]);
    setVideoUrl(null);
    setVideoTitle(null);
    setVideoDuration(0);
    setError(null);
  }, []);

  const generate = useCallback(async (params: GenerateParams) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setStatus("generating");
    setProgress(0);
    setScenes([]);
    setVideoUrl(null);
    setError(null);

    if (!params.google_api_key || params.google_api_key.trim() === "") {
      setError("Google API key is required. Please enter your Google API key.");
      setStatus("error");
      return;
    }

    if (!params.gmi_api_key || params.gmi_api_key.trim() === "") {
      setError("GMICloud API key is required. Please enter your GMI_API_KEY.");
      setStatus("error");
      return;
    }

    const validStyles: VideoStyle[] = ["cinematic", "anime", "cyberpunk", "watercolor", "fantasy", "noir"];
    if (!params.style || !validStyles.includes(params.style)) {
      setError(`Invalid style. Must be one of: ${validStyles.join(", ")}`);
      setStatus("error");
      return;
    }

    if (!params.voice || params.voice.trim() === "") {
      setError("Voice is required. Please select a voice.");
      setStatus("error");
      return;
    }

    try {
      await streamMediaGeneration(
        {
          prompt: params.prompt,
          style: params.style,
          voice: params.voice,
          google_api_key: params.google_api_key,
          gmi_api_key: params.gmi_api_key,
          elevenlabs_api_key: params.elevenlabs_api_key,
        },
        {
          onStageStart: (stage) => {
            console.log(`Stage start: ${stage}`);
            const stageProgress: Record<string, number> = {
              "B0.reference": 10,
              "B1.keyframes": 25,
              "B2.media": 50,
              "C.compose": 85,
            };
            setProgress(stageProgress[stage] || 10);
          },

          onStageComplete: (stage) => {
            console.log(`Stage complete: ${stage}`);
            const stageProgress: Record<string, number> = {
              "B0.reference": 20,
              "B1.keyframes": 45,
              "B2.media": 80,
              "C.compose": 95,
            };
            setProgress(stageProgress[stage] || 50);
          },

          onSceneAsset: (event: SceneAssetEvent) => {
            setScenes((prev) => {
              const updated = [...prev];
              const existing = updated.find((s) => s.index === event.step_index);

              const assetData = {
                ...(event.media_type === "video/mp4"
                  ? { video_url: event.asset_url }
                  : { image_url: event.asset_url }),
              };

              if (existing) {
                Object.assign(existing, assetData);
                return updated;
              } else {
                const newScene: Scene = {
                  index: event.step_index,
                  caption: `Scene ${event.step_index + 1}`,
                  ...assetData,
                };
                updated.push(newScene);
                return updated.sort((a, b) => a.index - b.index);
              }
            });

            setProgress((p) => Math.min(p + 3, 90));
          },

          onComplete: (event: ComposeCompleteEvent) => {
            setVideoUrl(event.asset.url);
            setVideoTitle(event.spec.title);
            setVideoDuration(event.spec.total_duration_sec);
            setStatus("complete");
            setProgress(100);
          },

          onError: (event: ErrorEvent) => {
            setError(event.message);
            setStatus("error");
          },

          onNotice: (event: NoticeEvent) => {
            console.warn("Notice:", event.message);
          },
        }
      );
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        console.log("Generation aborted");
        return;
      }
      setError(err instanceof Error ? err.message : "Generation failed");
      setStatus("error");
    }
  }, []);

  return {
    generate,
    reset,
    status,
    progress,
    scenes,
    videoUrl,
    videoTitle,
    videoDuration,
    error,
  };
}