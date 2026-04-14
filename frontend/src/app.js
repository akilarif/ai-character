import { createAudioCapture } from "./audio-capture.js";
import { ELEMENT_IDS, MESSAGE_TYPES, STATES } from "./constants.js";
import { initializeModel } from "./model-controller.js";
import { createSocketClient } from "./socket-client.js";
import { createTtsPlaybackQueue } from "./tts-playback-queue.js";
import { createUiState } from "./ui-state.js";

export async function startApp() {
  const canvasLive2d = document.getElementById(ELEMENT_IDS.canvasLive2d);
  const btnAudioUnlock = document.getElementById(ELEMENT_IDS.btnAudioUnlock);
  const btnMic = document.getElementById(ELEMENT_IDS.btnMic);
  const divAiState = document.getElementById(ELEMENT_IDS.divAiState);
  const divAiStatus = document.getElementById(ELEMENT_IDS.divAiStatus);
  const divAudioStatus = document.getElementById(ELEMENT_IDS.divAudioStatus);

  const ui = createUiState({
    btnAudioUnlock,
    btnMic,
    divAiState,
    divAiStatus,
    divAudioStatus,
  });

  const { model } = await initializeModel(canvasLive2d);
  let isAiBusy = false;

  const ttsQueue = createTtsPlaybackQueue({
    model,
    onStateChange: (state) => {
      ui.setAiState(model, state);
      isAiBusy = state !== STATES.IDLE;
    },
    onQueueDrained: () => {
      if (!socketClient.safeSend({ type: MESSAGE_TYPES.AUDIO_DONE })) {
        ui.setAiState(model, STATES.IDLE);
        isAiBusy = false;
      }
    },
  });

  const socketClient = createSocketClient({
    onConnectionChange: (online) => ui.setConnection(online),
    onState: (data) => {
      if (!data?.state) return;
      if (data.state === STATES.IDLE && ttsQueue.hasPendingAudio()) {
        return;
      }

      ui.setAiState(model, data.state);
      isAiBusy = data.state !== STATES.LISTENING && data.state !== STATES.IDLE;
      if (data.state === STATES.SPEAKING) {
        console.log("User Text:", data.userText);
        console.log("LLM Response:", data.llmResponse);
      }
    },
    onAudio: (audioBuffer) => ttsQueue.enqueue(audioBuffer),
  });

  const audioCapture = createAudioCapture({
    onPcmChunk: (pcmBytes) => {
      if (!audioCapture.isActive() || isAiBusy) {
        return;
      }
      socketClient.safeSendBytes(pcmBytes);
    },
    onStarted: () => ui.setMicActive(true),
    onStopped: () => ui.setMicActive(false),
  });

  btnMic.onclick = async () => {
    if (!audioCapture.isActive()) {
      await audioCapture.start();
      return;
    }
    await audioCapture.stop();
    socketClient.safeSend({ type: MESSAGE_TYPES.MIC_STOPPED });
  };

  btnAudioUnlock.onclick = () => {
    if (PIXI.sound && PIXI.sound.context) {
      PIXI.sound.context.audioContext.resume();
    }
    ui.setAudioUnlocked();
  };

  socketClient.connect();
}
