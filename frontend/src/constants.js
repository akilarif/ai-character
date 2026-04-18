export const SERVER_CONFIG = Object.freeze({
  host: "localhost",
  port: 8100,
  maxReconnectDelayMs: 30000,
  baseReconnectDelayMs: 1000,
});

export const ELEMENT_IDS = Object.freeze({
  appShell: "app-shell",
  canvasLive2d: "canvas-live2d",
  btnMic: "btn-mic",
  divAudioStatus: "audio-status",
  divAiStatus: "ai-status",
  divAiState: "ai-state",
  divUserText: "user-text",
  divLlmResponse: "llm-response",
});

export const UI_TEXT = Object.freeze({
  BRAIN_ONLINE: "Brain Online",
  BRAIN_OFFLINE: "Brain Offline",
  AUDIO_UNLOCKED: "Audio Ready",
  AUDIO_LOCKED: "Audio will activate on first mic use",
  AUDIO_UNLOCK_FAILED: "Audio still needs a tap to enable playback",
  MIC_ON: "Mic On",
  MIC_OFF: "Mic Off",
  IDLE: "Idle",
  LISTENING: "Listening",
  THINKING: "Thinking",
  SPEAKING: "Speaking",
  USER_PLACEHOLDER:
    "Your finalized transcript will appear here after you finish speaking.",
  LLM_RESPONSE_PLACEHOLDER:
    "The character response will stream here while playback is in progress.",
});

export const STATES = Object.freeze({
  IDLE: "IDLE",
  LISTENING: "LISTENING",
  THINKING: "THINKING",
  SPEAKING: "SPEAKING",
});

export const MESSAGE_TYPES = Object.freeze({
  AUDIO_DONE: "AUDIO_DONE",
  MIC_STOPPED: "MIC_STOPPED",
});

/** Mic capture + PCM worklet (must match backend STT sample rate). */
export const AUDIO_CONFIG = Object.freeze({
  sampleRateHz: 16000,
  workletModuleUrl: "pcm-worklet.js",
  workletProcessorName: "pcm-processor",
});
