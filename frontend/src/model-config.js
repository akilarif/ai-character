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
