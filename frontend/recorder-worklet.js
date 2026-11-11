// No output is connected to the speakers: recorded microphone audio is never echoed.
class Recorder extends AudioWorkletProcessor {
    process(inputs) {
        const channel = inputs[0]?.[0];
        if (channel) this.port.postMessage(channel.slice());
        return true;
    }
}
registerProcessor("gpt-pi-recorder", Recorder);
