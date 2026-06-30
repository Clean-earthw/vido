/**
 * Thin REST + SSE client over the FastAPI backend.
 * Mirrors the vibe-coding-starter-kit's api-client.ts shape.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ============================================================================
// Types
// ============================================================================

export interface FileMetadata {
  key: string;
  size: number;
  last_modified?: string | null;
  run_id?: string;
  display_name?: string;
}

export interface HealthResponse {
  status: "healthy" | "degraded";
  b2_connected: boolean;
  ffmpeg_present: boolean;
  providers: {
    google: boolean;
    gmi: boolean;
    nvidia: boolean;
    elevenlabs: boolean;
    decart: boolean;
  };
}

export interface Scene {
  image_prompt: string;
  motion_prompt: string;
  narration: string;
  caption: string;
  duration_sec: number;
}

export interface StoryboardSpec {
  title: string;
  style_prompt: string;
  music_prompt: string;
  total_duration_sec: number;
  scenes: Scene[];
}

export interface StoryboardResponse {
  spec: StoryboardSpec;
  storyboard_key: string;
}

export interface GenerateRequest {
  prompt: string;
  style: "cinematic" | "anime" | "cyberpunk" | "watercolor" | "fantasy" | "noir";
  voice: "professional" | "enthusiastic" | "calm" | "dramatic" | "friendly";
  google_api_key: string;  // Required - user must provide their Google API key
  gmi_api_key: string;  // Required - user must provide their GMI API key
  elevenlabs_api_key?: string;  // Optional - uses default if not provided
}


export interface GenerateResponse {
  video_url: string;
  manifest_url: string;
  title: string;
  duration: number;
}


// ============================================================================
// SSE Event Types
// ============================================================================

export interface SSEEvent {
  kind: string;
  stage?: string;
  step_index?: number;
  asset_url?: string;
  media_type?: string;
  message?: string;
  code?: string;
  retryable?: boolean;
  hint?: string;
  event?: unknown;
}

export interface StageStartEvent extends SSEEvent {
  kind: "stage.start";
  stage: string;
}

export interface StageCompleteEvent extends SSEEvent {
  kind: "stage.complete";
  stage: string;
}

export interface SceneAssetEvent extends SSEEvent {
  kind: "scene.asset";
  stage: string;
  step_index: number;
  asset_url: string;
  media_type: string;
}

export interface ComposeCompleteEvent extends SSEEvent {
  kind: "compose.complete";
  asset: {
    url: string;
    media_type: string;
    sha256: string;
    size_bytes: number;
  };
  spec: StoryboardSpec;
  run_id: string;
  manifest_uri?: string;
}

export interface ErrorEvent extends SSEEvent {
  kind: "error";
  stage: string;
  code: string;
  message: string;
  hint: string;
  retryable: boolean;
}

export interface NoticeEvent extends SSEEvent {
  kind: "notice";
  stage: string;
  message: string;
}

export type SSEMessage =
  | StageStartEvent
  | StageCompleteEvent
  | SceneAssetEvent
  | ComposeCompleteEvent
  | ErrorEvent
  | NoticeEvent;

// ============================================================================
// Error Class
// ============================================================================

export class ApiError extends Error {
  readonly code?: string;
  readonly hint?: string;
  private readonly _retryable?: boolean;

  constructor(
    message: string,
    public readonly status: number,
    classified?: { code?: string; hint?: string; retryable?: boolean }
  ) {
    super(message);
    this.name = "ApiError";
    this.code = classified?.code;
    this.hint = classified?.hint;
    this._retryable = classified?.retryable;
  }

  get isRetryable(): boolean {
    if (typeof this._retryable === "boolean") return this._retryable;
    return [408, 429, 500, 502, 503, 504].includes(this.status);
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isConflict(): boolean {
    return this.status === 409;
  }
}

// ============================================================================
// API Client
// ============================================================================

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new ApiError("Network error — check your connection", 0);
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body?.detail;

    // 422 validation errors
    if (Array.isArray(detail)) {
      const first = detail[0];
      const field = Array.isArray(first?.loc)
        ? first.loc[first.loc.length - 1]
        : undefined;
      const msg = first?.msg
        ? `${field ? `${field}: ` : ""}${first.msg}`
        : `API error: ${res.status}`;
      throw new ApiError(msg, res.status);
    }

    // Classified error
    if (detail && typeof detail === "object") {
      throw new ApiError(
        detail.message || `API error: ${res.status}`,
        res.status,
        detail
      );
    }

    throw new ApiError(detail || `API error: ${res.status}`, res.status);
  }

  return res.json();
}

// ============================================================================
// Endpoints
// ============================================================================

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export async function getFiles(): Promise<FileMetadata[]> {
  const data = await apiFetch<{
    prefix: string;
    entries: FileMetadata[];
  }>("/files");

  return (data.entries ?? []).map((e) => {
    const m = e.key.match(/^explainers\/([^/]+)\/(.*)$/);
    return {
      ...e,
      run_id: m ? m[1] : undefined,
      display_name: m ? m[2] : e.key,
    };
  });
}

export async function getRunAssets(runId: string): Promise<FileMetadata[]> {
  const data = await apiFetch<{
    prefix: string;
    entries: FileMetadata[];
  }>(`/runs/${runId}/assets`);

  return (data.entries ?? []).map((e) => {
    const m = e.key.match(/^explainers\/([^/]+)\/(.*)$/);
    return {
      ...e,
      run_id: m ? m[1] : undefined,
      display_name: m ? m[2] : e.key,
    };
  });
}

export async function createStoryboard(
  prompt: string,
  style: string = "cinematic",
  voice: string = "professional"
): Promise<StoryboardResponse> {
  return apiFetch<StoryboardResponse>("/runs/storyboard", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, style, voice }),
  });
}

// ============================================================================
// SSE Stream for Media Generation
// ============================================================================

export interface StreamCallbacks {
  onStageStart?: (stage: string) => void;
  onStageComplete?: (stage: string) => void;
  onSceneAsset?: (event: SceneAssetEvent) => void;
  onProgress?: (progress: number) => void;
  onComplete?: (event: ComposeCompleteEvent) => void;
  onError?: (event: ErrorEvent) => void;
  onNotice?: (event: NoticeEvent) => void;
}

export async function streamMediaGeneration(
  request: GenerateRequest,
  callbacks: StreamCallbacks
): Promise<void> {
  const response = await fetch(`${API_BASE}/runs/media/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.body) {
    throw new Error("No response body from server");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6)) as SSEMessage;

            switch (data.kind) {
              case "stage.start":
                callbacks.onStageStart?.(data.stage);
                break;

              case "stage.complete":
                callbacks.onStageComplete?.(data.stage);
                break;

              case "scene.asset":
                callbacks.onSceneAsset?.(data as SceneAssetEvent);
                break;

              case "compose.complete":
                callbacks.onComplete?.(data as ComposeCompleteEvent);
                break;

              case "error":
                callbacks.onError?.(data as ErrorEvent);
                break;

              case "notice":
                callbacks.onNotice?.(data as NoticeEvent);
                break;
            }
          } catch (e) {
            console.error("Failed to parse SSE event:", e);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

// ============================================================================
// Utilities
// ============================================================================

/** Durable URL → playback URL via backend proxy */
export function playbackUrl(durableOrKey: string): string {
  if (!durableOrKey.startsWith("http")) {
    return `${API_BASE}/assets/${durableOrKey}`;
  }

  try {
    const u = new URL(durableOrKey);
    const trimmed = u.pathname.replace(/^\//, "");
    const slash = trimmed.indexOf("/");
    const key = slash === -1 ? trimmed : trimmed.slice(slash + 1);
    return `${API_BASE}/assets/${key}`;
  } catch {
    return durableOrKey;
  }
}

/** Format duration in seconds to MM:SS */
export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return mins > 0 ? `${mins}:${secs.toString().padStart(2, "0")}` : `${secs}s`;
}

/** Truncate text with ellipsis */
export function truncateText(text: string, maxLength: number = 60): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + "...";
}

/** Format file size */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)}GB`;
}