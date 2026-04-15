import { STATES, UI_TEXT } from "./constants.js";
import { applyModelState } from "./model-controller.js";

export function createUiState({
  appShell,
  btnMic,
  divAiState,
  divAiStatus,
  divAudioStatus,
  divUserText,
  divLlmResponse,
}) {
  function setConnection(online) {
    divAiStatus.innerText = online
      ? UI_TEXT.BRAIN_ONLINE
      : UI_TEXT.BRAIN_OFFLINE;
    divAiStatus.dataset.online = online ? "true" : "false";
  }

  function setAudioUnlocked(unlocked) {
    divAudioStatus.innerText = unlocked
      ? UI_TEXT.AUDIO_UNLOCKED
      : UI_TEXT.AUDIO_LOCKED;
    divAudioStatus.dataset.locked = unlocked ? "false" : "true";
  }

  function setAudioUnlockFailed() {
    divAudioStatus.innerText = UI_TEXT.AUDIO_UNLOCK_FAILED;
    divAudioStatus.dataset.locked = "true";
  }

  function setMicEnabled(enabled) {
    btnMic.disabled = !enabled;
    btnMic.dataset.enabled = enabled ? "true" : "false";
  }

  function setMicActive(active) {
    btnMic.innerText = active ? UI_TEXT.MIC_ON : UI_TEXT.MIC_OFF;
    btnMic.dataset.active = active ? "true" : "false";
    btnMic.setAttribute("aria-pressed", active ? "true" : "false");
  }

  function initializeControls() {
    setAudioUnlocked(false);
    setMicEnabled(true);
    setMicActive(false);
  }

  function setAiState(model, state) {
    switch (state) {
      case STATES.LISTENING:
        divAiState.innerText = UI_TEXT.LISTENING;
        break;
      case STATES.THINKING:
        divAiState.innerText = UI_TEXT.THINKING;
        break;
      case STATES.SPEAKING:
        divAiState.innerText = UI_TEXT.SPEAKING;
        break;
      case STATES.IDLE:
      default:
        divAiState.innerText = UI_TEXT.IDLE;
        break;
    }
    divAiState.dataset.state = state.toLowerCase();
    appShell.dataset.aiState = state.toLowerCase();
    applyModelState(model, state);
  }

  function setUserText(text) {
    const normalizedText = text?.trim() ?? "";
    divUserText.innerText = normalizedText || UI_TEXT.USER_PLACEHOLDER;
    divUserText.dataset.empty = normalizedText ? "false" : "true";
  }

  function setLlmResponse(text, { streaming = false } = {}) {
    const normalizedText = text?.trim() ?? "";
    divLlmResponse.innerText =
      normalizedText || UI_TEXT.LLM_RESPONSE_PLACEHOLDER;
    divLlmResponse.dataset.empty = normalizedText ? "false" : "true";
    divLlmResponse.dataset.streaming = streaming ? "true" : "false";
  }

  return {
    initializeControls,
    setConnection,
    setAudioUnlocked,
    setAudioUnlockFailed,
    setMicEnabled,
    setMicActive,
    setAiState,
    setUserText,
    setLlmResponse,
  };
}
