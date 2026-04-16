import { createAudioCapture } from "./audio-capture.js";
import { ELEMENT_IDS, MESSAGE_TYPES, STATES } from "./constants.js";
import { initializeModel } from "./model-controller.js";
import { createSocketClient } from "./socket-client.js";
import { createTtsPlaybackQueue } from "./tts-playback-queue.js";
import { createUiState } from "./ui-state.js";

export async function startApp() {
  const appShell = document.getElementById(ELEMENT_IDS.appShell);
  const canvasLive2d = document.getElementById(ELEMENT_IDS.canvasLive2d);
  const btnMic = document.getElementById(ELEMENT_IDS.btnMic);
  const divAiState = document.getElementById(ELEMENT_IDS.divAiState);
  const divAiStatus = document.getElementById(ELEMENT_IDS.divAiStatus);
  const divAudioStatus = document.getElementById(ELEMENT_IDS.divAudioStatus);
  const divUserText = document.getElementById(ELEMENT_IDS.divUserText);
  const divLlmResponse = document.getElementById(ELEMENT_IDS.divLlmResponse);

  const ui = createUiState({
    appShell,
    btnMic,
    divAiState,
    divAiStatus,
    divAudioStatus,
    divUserText,
    divLlmResponse,
  });

  const { model } = await initializeModel(canvasLive2d);
  let isAiBusy = false;
  const currentTurn = {
    userText: "",
    llmResponse: "",
    emotion: null,
  };

  ui.initializeControls();
  ui.setUserText("");
  ui.setLlmResponse("");

  const ttsQueue = createTtsPlaybackQueue({
    model,
    onStateChange: (state, emotion) => {
      ui.setAiState(model, state, emotion);
      isAiBusy = state !== STATES.IDLE;
    },
    onQueueDrained: () => {
      if (!socketClient.safeSend({ type: MESSAGE_TYPES.AUDIO_DONE })) {
        ui.setAiState(model, STATES.IDLE, null);
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

      currentTurn.emotion = null;

      if (data.state === STATES.THINKING) {
        currentTurn.userText = data.userText?.trim?.() || currentTurn.userText;
        currentTurn.llmResponse = "";
        if (currentTurn.userText) {
          ui.setUserText(currentTurn.userText);
        }
        ui.setLlmResponse("");
      }

      if (data.state === STATES.SPEAKING) {
        if (typeof data.userText === "string" && data.userText.trim()) {
          currentTurn.userText = data.userText.trim();
          ui.setUserText(currentTurn.userText);
        }
        if (
          typeof data.llmResponse === "string" &&
          data.llmResponse.length > 0
        ) {
          currentTurn.llmResponse = appendLlmResponse(
            currentTurn.llmResponse,
            data.llmResponse,
          );
          ui.setLlmResponse(currentTurn.llmResponse, { streaming: true });
        }
        if (typeof data.emotion === "string" && data.emotion.trim()) {
          currentTurn.emotion = data.emotion.trim();
        }
      }

      if (data.state === STATES.IDLE) {
        ui.setLlmResponse(currentTurn.llmResponse, { streaming: false });
      }

      // State updates for speaking is handled in ttsQueue
      if (data.state !== STATES.SPEAKING) {
        ui.setAiState(model, data.state, currentTurn.emotion);
      }
      isAiBusy = data.state !== STATES.LISTENING && data.state !== STATES.IDLE;
    },
    onAudio: (audioBuffer) =>
      ttsQueue.enqueue(audioBuffer, currentTurn.emotion),
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
    ui.setMicEnabled(false);
    if (!audioCapture.isActive()) {
      const audioReady = await ensurePlaybackReady();
      if (!audioReady) {
        ui.setAudioUnlockFailed();
        ui.setMicEnabled(true);
        return;
      }
      ui.setAudioUnlocked(true);
      await audioCapture.start();
      ui.setMicEnabled(true);
      return;
    }
    await audioCapture.stop();
    socketClient.safeSend({ type: MESSAGE_TYPES.MIC_STOPPED });
    ui.setMicEnabled(true);
  };

  socketClient.connect();
}

function appendLlmResponse(currentText, nextChunk) {
  const normalizedChunk = nextChunk.trim();
  if (!normalizedChunk) {
    return currentText;
  }
  if (!currentText) {
    return normalizedChunk;
  }

  const needsSpacer =
    !/[\s(\[{/-]$/.test(currentText) && !/^[,.;:!?)}\]]/.test(normalizedChunk);
  return `${currentText}${needsSpacer ? " " : ""}${normalizedChunk}`;
}

async function ensurePlaybackReady() {
  const audioContext = PIXI.sound?.context?.audioContext;
  if (!audioContext) {
    return true;
  }

  if (audioContext.state === "running") {
    return true;
  }

  try {
    await audioContext.resume();
    return audioContext.state === "running";
  } catch (error) {
    console.error("Failed to unlock audio playback:", error);
    return false;
  }
}
