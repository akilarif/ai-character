export const MODEL_CONFIG = Object.freeze({
  modelDir: "models/Haru",
  modelPath: "models/Haru/Haru.model3.json",
  shouldPlayMotionSounds: false,
});

/**
 * Live2D motion/expression mapping (see model motions under MODEL_CONFIG.modelDir).
 * motion: [groupName, indexInGroup, priority] — priority is 0 (lowest) to 3 (highest).
 */
export const LIVE2D_PRESENTATION = Object.freeze({
  expressions: Object.freeze({
    neutral: "F01",
    thinking: "F05",
  }),
  motionGroup: Object.freeze({
    idle: "Idle",
  }),
  /** motion + expression per UI/server conversation state */
  byConversationState: Object.freeze({
    IDLE: Object.freeze({
      expressionKey: "neutral",
      motion: Object.freeze(["idle", 0, 1]),
    }),
    LISTENING: Object.freeze({
      expressionKey: "neutral",
      motion: Object.freeze(["idle", 0, 3]),
    }),
    THINKING: Object.freeze({
      expressionKey: "thinking",
      motion: Object.freeze(["idle", 1, 0]),
    }),
    SPEAKING: Object.freeze({
      expressionKey: "neutral",
      motion: null,
    }),
  }),
});

export const SERVER_CONFIG = Object.freeze({
  host: "localhost",
  port: 8100,
  maxReconnectDelayMs: 30000,
  baseReconnectDelayMs: 1000,
});

export const ELEMENT_IDS = Object.freeze({
  canvasLive2d: "canvas-live2d",
  btnAudioUnlock: "btn-audio-unlock",
  btnMic: "btn-mic",
  divAudioStatus: "audio-status",
  divAiStatus: "ai-status",
  divAiState: "ai-state",
});

export const UI_TEXT = Object.freeze({
  BRAIN_ONLINE: "Brain Online",
  BRAIN_OFFLINE: "Brain Offline",
  AUDIO_UNLOCKED: "Audio Status: Unlocked",
  AUDIO_LOCKED: "Audio Status: Locked",
  MIC_ON: "Mic: ON",
  MIC_OFF: "Mic: OFF",
  IDLE: "Idle",
  LISTENING: "Listening",
  THINKING: "Thinking",
  SPEAKING: "Speaking",
});

export const UI_COLORS = Object.freeze({
  ONLINE: "#00ff00",
  OFFLINE: "#ff0000",
  MIC_ON: "#2e7d32",
  MIC_OFF: "#444",
  AUDIO_UNLOCKED: "greenyellow",
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
