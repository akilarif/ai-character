import { STATES } from "./constants.js";

export function createTtsPlaybackQueue({
  model,
  onStateChange,
  onQueueDrained,
}) {
  const queue = []; // Contains objects of audio buffer and emotion
  let isPlaying = false;

  function enqueue(arrayBuffer, emotion) {
    queue.push({ arrayBuffer: arrayBuffer, emotion: emotion });
    void processQueue();
  }

  function hasPendingAudio() {
    return isPlaying || queue.length > 0;
  }

  async function processQueue() {
    if (isPlaying || queue.length === 0) return;

    isPlaying = true;
    const item = queue.shift();
    const currentAudio = item.arrayBuffer;
    const currentEmotion = item.emotion;

    onStateChange(STATES.SPEAKING, currentEmotion);
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
    if (model?.internalModel?.motionManager?.currentAudio) {
      model.internalModel.motionManager.currentAudio = null;
    }
    if (PIXI.sound.exists(alias)) {
      PIXI.sound.remove(alias);
    }
    URL.revokeObjectURL(audioUrl);
    cleanedUp = true;
  };

  try {
    await new Promise((resolve) => {
      PIXI.sound.add(alias, {
        url: audioUrl,
        preload: true,
        loaded: (error, sound) => {
          if (error || !sound || sound.duration === 0) {
            console.error("Failed to load TTS sound:", error);
            resolve();
            return;
          }

          model.internalModel.motionManager.initializeAudio(sound, 1.0);
          sound.play(() => {
            // Delay resolution by 100ms to let the audio buffer "drain"
            setTimeout(resolve, 100);
          });
        },
      });
    });
  } finally {
    cleanup();
  }
}
