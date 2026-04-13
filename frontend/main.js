var MODEL_DIR = "models/Haru";
var MODEL_PATH = `${MODEL_DIR}/Haru.model3.json`;

var SHOULD_PLAY_MOTION_SOUNDS = false;

var HOST = "localhost";
var PORT = 8100;

var model;
var socket;

let micActive = false;
let isAiBusy = false;

let localStream = null;
let audioContext = null;
let workletNode = null;
let sourceNode = null;

let ttsAudioQueue = [];
let isTtsAudioPlaying = false;

var Live2DModel = window.PIXI.live2d.Live2DModel;

const canvasLive2d = document.getElementById("live2d");

const btnAudioUnlock = document.getElementById("btn-audio-unlock");
const btnMic = document.getElementById("btn-mic");

const divAudioStatus = document.getElementById("audio-status");
const divAiStatus = document.getElementById("ai-status");
const divAiState = document.getElementById("ai-state");

async function init() {
  const app = new PIXI.Application();
  await app.init({
    canvas: canvasLive2d,
    resizeTo: window,
    backgroundAlpha: 0,
    antialias: true,
    autoDensity: true,
    resolution: window.devicePixelRatio || 1,
    preference: "webgl",
  });

  try {
    console.log("Loading model...");
    model = await Live2DModel.from(MODEL_PATH, {
      autoHitTest: true,
      autoFocus: true,
      autoUpdate: true,
    });

    setupMotionSounds();
    if (SHOULD_PLAY_MOTION_SOUNDS) {
      playMotionSound();
    }

    app.stage.addChild(model);

    // Position & Scale
    model.anchor.set(0.5);
    model.scale.set(0.15);
    model.x = app.screen.width / 2;
    model.y = app.screen.height / 2;

    console.log("Model is Ready!");
  } catch (e) {
    console.error("Model Load Error:", e);
  }

  setupWebSocket();
}

// Strips crashing audio metadata and pre-loads sounds into PIXI.sound
function setupMotionSounds() {
  const motions = model.internalModel.settings.motions;
  if (!motions) return;

  console.log("Setting up model audio...");
  // Pre-register sounds to prevent the pixi-sound errors "Assertion failed: Sound with alias url already exists., ..."
  for (const group in motions) {
    motions[group].forEach((motionData) => {
      if (motionData.Sound) {
        // Store the path in a new custom variable so it doesn't crash the loader
        motionData.customSoundPath = MODEL_DIR + "/" + motionData.Sound;
        // Pre-load it into PIXI.sound using the path as the alias
        if (!PIXI.sound.exists(motionData.customSoundPath)) {
          PIXI.sound.add(
            motionData.customSoundPath,
            motionData.customSoundPath,
          );
        }
        // Delete the original Sound key to prevent the "url already exists" crash
        delete motionData.Sound;
      }
    });
  }
}

function playMotionSound() {
  // Manually set the motion manager's task to play the sound
  model.internalModel.motionManager.on("motionStart", (group, index) => {
    const motionData = model.internalModel.settings.motions[group][index];
    if (motionData && motionData.customSoundPath) {
      console.log("Playing audio:", motionData.customSoundPath);
      // Use a slight timeout or resume to ensure the audio context is active
      PIXI.sound.play(motionData.customSoundPath, {
        singleInstance: false, // Allows overlapping sounds if needed
        volume: 1.0,
      });
    }
  });
}

function setupWebSocket() {
  socket = new WebSocket(`ws://${HOST}:${PORT}/ws`);

  socket.onopen = () => {
    divAiStatus.innerText = "Brain Online";
    divAiStatus.style.color = "#00ff00";
  };

  socket.onclose = () => {
    divAiStatus.innerText = "Brain Offline";
    divAiStatus.style.color = "#ff0000";
    setTimeout(setupWebSocket, 5000);
  };

  socket.onmessage = async (event) => {
    if (typeof event.data === "string") {
      try {
        const data = JSON.parse(event.data);
        handleJsonDataState(data);
      } catch (err) {
        console.error(
          "Failed to parse JSON for message: ",
          event.data,
          " . Error: ",
          err,
        );
      }
    } else {
      const arrayBuffer =
        event.data instanceof Blob
          ? await event.data.arrayBuffer()
          : event.data;
      ttsAudioQueue.push(arrayBuffer);
      processQueue();
    }
  };
}

function handleJsonDataState(data) {
  if (!model) return;

  switch (data.state) {
    case "LISTENING":
      isAiBusy = false;
      divAiState.innerText = "Listening";
      // Neutral alert face
      model.expression("F01");
      // Standard breathing idle
      // model.motion(group, id, priority)
      // priority- 0 (lowest) to 3 (highest)
      model.motion("Idle", 0, 3);
      break;
    case "THINKING":
      isAiBusy = true;
      divAiState.innerText = "Thinking";
      // Smiling with eyes closed
      model.expression("F05");
      // Secondary idle (m15) which usually has a head tilt
      model.motion("Idle", 1, 0);
      break;
    case "SPEAKING":
      isAiBusy = true;
      divAiState.innerText = "Speaking";
      console.log("User Text:", data.userText);
      console.log("LLM Response:", data.llmResponse);
      // Neutral alert face
      model.expression("F01");
      break;
    case "IDLE":
      if (!isTtsAudioPlaying && ttsAudioQueue.length === 0) {
        isAiBusy = false;
        divAiState.innerText = "Idle";
        // Reset to default neutral face
        model.expression("F01");
        model.motion("Idle", 0, 1);
      }
      break;
    default:
      console.warn("Unknown state:", data.state);
  }
}

async function processQueue() {
  if (isTtsAudioPlaying || ttsAudioQueue.length === 0) return;

  isAiBusy = true;
  isTtsAudioPlaying = true;
  divAiState.innerText = "Speaking";
  const currentAudio = ttsAudioQueue.shift();

  try {
    await speakAudio(currentAudio);
  } catch (err) {
    console.error("Playback error:", err);
  } finally {
    isTtsAudioPlaying = false;
    if (ttsAudioQueue.length === 0) {
      socket.send(JSON.stringify({ type: "AUDIO_DONE" }));
      isAiBusy = false;
      divAiState.innerText = "Idle";
    } else {
      processQueue();
    }
  }
}

async function toggleMic() {
  if (!micActive) {
    startStreamingAudioFromMic();
  } else {
    stopStreamingAudioFromMic();
  }
}

async function startStreamingAudioFromMic() {
  try {
    localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new AudioContext({ sampleRate: 16000 });
    await audioContext.audioWorklet.addModule("pcm-worklet.js");

    sourceNode = audioContext.createMediaStreamSource(localStream);
    workletNode = new AudioWorkletNode(audioContext, "pcm-processor");

    workletNode.port.onmessage = (event) => {
      if (micActive && !isAiBusy && socket?.readyState === WebSocket.OPEN) {
        socket.send(event.data); // raw PCM bytes
      }
    };

    sourceNode.connect(workletNode);
    workletNode.connect(audioContext.destination);

    micActive = true;
    btnMic.innerText = "Mic: ON";
    btnMic.style.backgroundColor = "#2e7d32";
    console.log("Streaming from mic started");
  } catch (err) {
    console.error("Mic Error:", err);
  }
}

async function stopStreamingAudioFromMic() {
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

  micActive = false;
  btnMic.innerText = "Mic: OFF";
  btnMic.style.backgroundColor = "#444";
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: "MIC_STOPPED" }));
  }
  console.log("Streaming from mic stopped");
}

async function speakAudio(arrayBuffer) {
  if (!model || !arrayBuffer) return;

  const alias = `voice_${Date.now()}_${Math.floor(Math.random() * 1000)}`;

  // Create a temporary PIXI.sound.Sound from ArrayBuffer
  return new Promise(async (resolve) => {
    try {
      // Wrap the ArrayBuffer into a Blob
      const blob = new Blob([arrayBuffer], { type: "audio/wav" });
      const audioUrl = URL.createObjectURL(blob);

      // Create PIXI.sound.Sound using the Blob URL
      PIXI.sound.add(alias, {
        url: audioUrl,
        preload: true,
        loaded: (err, sound) => {
          if (err) {
            console.error("Failed to load sound from bytes: ", err);
            URL.revokeObjectURL(audioUrl);
            return resolve(); // This triggers the 'await' in onmessage; We "resolve" anyway so the AI returns to IDLE state
          }

          model.internalModel.motionManager.initializeAudio(sound, 1.0);
          // Play and remove after finished
          sound.play(() => {
            console.log("Audio Playback Finished!");
            PIXI.sound.remove(alias);
            URL.revokeObjectURL(audioUrl);
            resolve();
          });
        },
      });
    } catch (err) {
      console.error("Error playing audio bytes: ", err);
      resolve();
    }
  });
}

// UI Handlers
btnAudioUnlock.onclick = () => {
  if (PIXI.sound && PIXI.sound.context) {
    PIXI.sound.context.audioContext.resume();
  }
  btnAudioUnlock.style.display = "none";
  btnMic.style.display = "inline-block";
  console.log("Audio Unlocked");
  divAudioStatus.style.color = "greenyellow";
  divAudioStatus.innerText = "Audio Status: Unlocked";
};

btnMic.onclick = toggleMic;

window.onload = init;
