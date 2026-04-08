class PcmProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;

    const channel = input[0]; // mono

    // Convert Float32 [-1,1] → Int16
    const pcm16 = new Int16Array(channel.length);
    for (let i = 0; i < channel.length; i++) {
      pcm16[i] = Math.max(-1, Math.min(1, channel[i])) * 0x7fff;
    }

    this.port.postMessage(pcm16.buffer, [pcm16.buffer]);
    return true;
  }
}

registerProcessor("pcm-processor", PcmProcessor);
