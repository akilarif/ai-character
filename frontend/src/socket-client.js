import { SERVER_CONFIG } from "./constants.js";

export function createSocketClient({ onState, onAudio, onConnectionChange }) {
  let socket = null;
  let reconnectAttempts = 0;
  let reconnectTimer = null;
  let stopped = false;

  function connect() {
    clearReconnectTimer();
    stopped = false;
    socket = new WebSocket(
      `ws://${SERVER_CONFIG.host}:${SERVER_CONFIG.port}/ws`,
    );

    socket.onopen = () => {
      reconnectAttempts = 0;
      onConnectionChange(true);
    };

    socket.onclose = () => {
      onConnectionChange(false);
      if (!stopped) {
        scheduleReconnect();
      }
    };

    socket.onmessage = async (event) => {
      if (typeof event.data === "string") {
        try {
          onState(JSON.parse(event.data));
        } catch (error) {
          console.error("Failed to parse websocket JSON payload:", error);
        }
        return;
      }

      const arrayBuffer =
        event.data instanceof Blob
          ? await event.data.arrayBuffer()
          : event.data;
      onAudio(arrayBuffer);
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }

  function stop() {
    stopped = true;
    clearReconnectTimer();
    if (socket) {
      socket.close();
    }
  }

  function isOpen() {
    return socket?.readyState === WebSocket.OPEN;
  }

  function safeSend(payload) {
    if (!isOpen()) {
      return false;
    }
    const body =
      typeof payload === "string" ? payload : JSON.stringify(payload);
    socket.send(body);
    return true;
  }

  function safeSendBytes(payload) {
    if (!isOpen()) {
      return false;
    }
    socket.send(payload);
    return true;
  }

  // Exponential backoff with jitter
  function scheduleReconnect() {
    reconnectAttempts += 1;
    const base =
      SERVER_CONFIG.baseReconnectDelayMs * 2 ** (reconnectAttempts - 1);
    const jitter = Math.floor(Math.random() * 300);
    const delayMs = Math.min(base + jitter, SERVER_CONFIG.maxReconnectDelayMs);
    reconnectTimer = window.setTimeout(connect, delayMs);
  }

  function clearReconnectTimer() {
    if (reconnectTimer) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  }

  return {
    connect,
    stop,
    safeSend,
    safeSendBytes,
    isOpen,
  };
}
