import { LIVE2D_PRESENTATION, MODEL_CONFIG } from "./constants.js";

const Live2DModel = window.PIXI.live2d.Live2DModel;

export async function initializeModel(canvasElement) {
  const app = new PIXI.Application();
  const viewportElement = canvasElement.parentElement ?? window;
  await app.init({
    canvas: canvasElement,
    resizeTo: viewportElement,
    backgroundAlpha: 0,
    antialias: true,
    autoDensity: true,
    resolution: window.devicePixelRatio || 1,
    preference: "webgl",
  });

  const model = await Live2DModel.from(MODEL_CONFIG.modelPath, {
    autoHitTest: true,
    autoFocus: true,
    autoUpdate: true,
  });

  setupMotionSounds(model);
  if (MODEL_CONFIG.shouldPlayMotionSounds) {
    playMotionSound(model);
  }

  app.stage.addChild(model);

  // Position & Scale
  model.anchor.set(0.5);
  model.scale.set(0.15);
  model.x = app.screen.width / 2;
  model.y = app.screen.height / 2;

  return { app, model };
}

export function applyModelState(model, state, emotion = null) {
  if (!model) {
    return;
  }

  let preset;
  if (
    state === "SPEAKING" &&
    emotion &&
    LIVE2D_PRESENTATION.byEmotion[emotion]
  ) {
    preset = LIVE2D_PRESENTATION.byEmotion[emotion];
  } else {
    preset = LIVE2D_PRESENTATION.byConversationState[state];
  }
  if (!preset) {
    return;
  }

  const expressionId = LIVE2D_PRESENTATION.expressions[preset.expressionKey];
  if (expressionId) {
    model.expression(expressionId);
  }

  if (!preset.motion) {
    return;
  }
  const [motionGroupKey, motionIndex, priority] = preset.motion;
  const groupName = LIVE2D_PRESENTATION.motionGroup[motionGroupKey];
  if (groupName) {
    model.motion(groupName, motionIndex, priority);
  }
}

// Strips crashing audio metadata and pre-loads sounds into PIXI.sound
function setupMotionSounds(model) {
  const motions = model.internalModel.settings.motions;
  if (!motions) return;
  // Pre-register sounds to prevent the pixi-sound errors like
  // "Assertion failed: Sound with alias url already exists."
  for (const group in motions) {
    motions[group].forEach((motionData) => {
      if (!motionData.Sound) return;
      motionData.customSoundPath = `${MODEL_CONFIG.modelDir}/${motionData.Sound}`;
      if (!PIXI.sound.exists(motionData.customSoundPath)) {
        PIXI.sound.add(motionData.customSoundPath, motionData.customSoundPath);
      }
      // Delete the original Sound key to prevent the "url already exists" crash
      delete motionData.Sound;
    });
  }
}

function playMotionSound(model) {
  // Manually set the motion manager's task to play the sound
  model.internalModel.motionManager.on("motionStart", (group, index) => {
    const motionData = model.internalModel.settings.motions[group][index];
    if (motionData?.customSoundPath) {
      PIXI.sound.play(motionData.customSoundPath, {
        singleInstance: false,
        volume: 1.0,
      });
    }
  });
}
