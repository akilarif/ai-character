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
    happy: "F01",
    openMouth: "F02",
    angry: "F03",
    sad: "F04",
    smile: "F05",
    surprised: "F06",
    blush: "F07",
    frown: "F08",
  }),
  motionGroup: Object.freeze({
    idle: "Idle",
    tapBody: "TapBody",
  }),
  /** motion + expression per UI/server conversation state */
  byConversationState: Object.freeze({
    IDLE: Object.freeze({
      expressionKey: "neutral",
      motion: Object.freeze(["idle", 0, 3]),
    }),
    LISTENING: Object.freeze({
      expressionKey: "neutral",
      motion: Object.freeze(["idle", 0, 3]),
    }),
    THINKING: Object.freeze({
      expressionKey: "smile",
      motion: Object.freeze(["idle", 1, 0]),
    }),
    SPEAKING: Object.freeze({
      expressionKey: "neutral",
      motion: null,
    }),
  }),
  /** Mapping for [emotion] tags from the pipeline */
  byEmotion: Object.freeze({
    neutral: Object.freeze({
      expressionKey: "neutral",
      motion: null,
    }),
    happy: Object.freeze({
      expressionKey: "happy",
      motion: Object.freeze(["tapBody", 1, 3]),
      // motion: null,
    }),
    angry: Object.freeze({
      expressionKey: "angry",
      motion: null,
    }),
    sad: Object.freeze({
      expressionKey: "sad",
      motion: Object.freeze(["tapBody", 2, 3]),
    }),
    smile: Object.freeze({
      expressionKey: "smile",
      motion: null,
    }),
    surprised: Object.freeze({
      expressionKey: "surprised",
      motion: null,
    }),
    blush: Object.freeze({
      expressionKey: "blush",
      motion: Object.freeze(["tapBody", 0, 3]),
    }),
    frown: Object.freeze({
      expressionKey: "frown",
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
