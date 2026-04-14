import { STATES, UI_COLORS, UI_TEXT } from "./constants.js";
import { applyModelState } from "./model-controller.js";

export function createUiState({
  btnAudioUnlock,
  btnMic,
  divAiState,
  divAiStatus,
  divAudioStatus,
}) {
  function setConnection(online) {
    divAiStatus.innerText = online
      ? UI_TEXT.BRAIN_ONLINE
      : UI_TEXT.BRAIN_OFFLINE;
    divAiStatus.style.color = online ? UI_COLORS.ONLINE : UI_COLORS.OFFLINE;
  }

  function setAudioUnlocked() {
    btnAudioUnlock.style.display = "none";
    btnMic.style.display = "inline-block";
    divAudioStatus.style.color = UI_COLORS.AUDIO_UNLOCKED;
    divAudioStatus.innerText = UI_TEXT.AUDIO_UNLOCKED;
  }

  function setMicActive(active) {
    btnMic.innerText = active ? UI_TEXT.MIC_ON : UI_TEXT.MIC_OFF;
    btnMic.style.backgroundColor = active
      ? UI_COLORS.MIC_ON
      : UI_COLORS.MIC_OFF;
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
    applyModelState(model, state);
  }

  return {
    setConnection,
    setAudioUnlocked,
    setMicActive,
    setAiState,
  };
}
