import { STATES } from "./constants.js";

export function createTtsPlaybackQueue({
  model,
  onStateChange,
  onQueueDrained,
}) {
  const queue = [];
  let isPlaying = false;

  function enqueue(arrayBuffer) {
    queue.push(arrayBuffer);
    void processQueue();
  }

  function hasPendingAudio() {
    return isPlaying || queue.length > 0;
  }

  async function processQueue() {
    if (isPlaying || queue.length === 0) return;

    isPlaying = true;
    onStateChange(STATES.SPEAKING);

    const currentAudio = queue.shift();
    try {
      await speakAudio(model, currentAudio);
    } catch (error) {
      console.error("Playback error:", error);
    } finally {
      isPlaying = false;
      if (queue.length > 0) {
        void processQueue();
        return;
      }
      onQueueDrained();
    }
  }

  return {
    enqueue,
    hasPendingAudio,
  };
}

async function speakAudio(model, arrayBuffer) {
  if (!model || !arrayBuffer) return;

  const alias = `voice_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
  const blob = new Blob([arrayBuffer], { type: "audio/wav" });
  const audioUrl = URL.createObjectURL(blob);
  let cleanedUp = false;

  const cleanup = () => {
    if (cleanedUp) return;
    cleanedUp = true;
    if (PIXI.sound.exists(alias)) {
      PIXI.sound.remove(alias);
    }
    URL.revokeObjectURL(audioUrl);
  };

  try {
    await new Promise((resolve) => {
      PIXI.sound.add(alias, {
        url: audioUrl,
        preload: true,
        loaded: (error, sound) => {
          if (error) {
            console.error("Failed to load TTS sound:", error);
            cleanup();
            resolve();
            return;
          }

          model.internalModel.motionManager.initializeAudio(sound, 1.0);
          sound.play(() => {
            cleanup();
            resolve();
          });
        },
      });
    });
  } finally {
    cleanup();
  }
}
