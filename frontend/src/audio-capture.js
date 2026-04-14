import { AUDIO_CONFIG } from "./constants.js";

export function createAudioCapture({ onPcmChunk, onStarted, onStopped }) {
  let isMicActive = false;
  let localStream = null;
  let audioContext = null;
  let workletNode = null;
  let sourceNode = null;

  async function start() {
    if (isMicActive) {
      return;
    }

    try {
      localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContext = new AudioContext({
        sampleRate: AUDIO_CONFIG.sampleRateHz,
      });
      await audioContext.audioWorklet.addModule(AUDIO_CONFIG.workletModuleUrl);

      sourceNode = audioContext.createMediaStreamSource(localStream);
      workletNode = new AudioWorkletNode(
        audioContext,
        AUDIO_CONFIG.workletProcessorName,
      );

      workletNode.port.onmessage = (event) => {
        onPcmChunk(event.data);
      };

      sourceNode.connect(workletNode);
      workletNode.connect(audioContext.destination);

      isMicActive = true;
      onStarted();
    } catch (error) {
      console.error("Mic error:", error);
    }
  }

  async function stop() {
    if (!isMicActive && !audioContext) {
      return;
    }

    if (workletNode) workletNode.disconnect();
    if (sourceNode) sourceNode.disconnect();
    if (audioContext) {
      await audioContext.close();
      audioContext = null;
    }
    if (localStream) {
      localStream.getTracks().forEach((track) => track.stop());
    }

    workletNode = null;
    sourceNode = null;
    localStream = null;
    isMicActive = false;
    onStopped();
  }

  function isActive() {
    return isMicActive;
  }

  return {
    start,
    stop,
    isActive,
  };
}
