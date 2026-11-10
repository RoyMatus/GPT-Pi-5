export function pcmWave(chunks, sampleRate) {
    const total = chunks.reduce((n, chunk) => n + chunk.length, 0);
    const input = new Float32Array(total);
    let offset = 0;
    for (const chunk of chunks) { input.set(chunk, offset); offset += chunk.length; }
    const length = Math.min(480000, Math.floor(total * 16000 / sampleRate));
    const buffer = new ArrayBuffer(44 + length * 2);
    const view = new DataView(buffer);
    const word = (at, text) => [...text].forEach((c, i) => view.setUint8(at + i, c.charCodeAt(0)));
    word(0, "RIFF"); view.setUint32(4, buffer.byteLength - 8, true); word(8, "WAVE");
    word(12, "fmt "); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, 1, true); view.setUint32(24, 16000, true);
    view.setUint32(28, 32000, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
    word(36, "data"); view.setUint32(40, length * 2, true);
    for (let i = 0; i < length; i++) {
        const start = Math.floor(i * sampleRate / 16000);
        const end = Math.min(total, Math.max(start + 1, Math.floor((i + 1) * sampleRate / 16000)));
        let sum = 0;
        for (let j = start; j < end; j++) sum += input[j];
        const value = Math.max(-1, Math.min(1, sum / (end - start)));
        view.setInt16(44 + i * 2, value * (value < 0 ? 32768 : 32767), true);
    }
    return new Blob([buffer], { type: "audio/wav" });
}

export class Microphone {
    constructor({ mediaDevices = navigator.mediaDevices, Context = AudioContext } = {}) {
        this.mediaDevices = mediaDevices;
        this.Context = Context;
        this.generation = 0;
        this.chunks = [];
    }
    async start(onLimit, onEnded) {
        this.cancel();
        const generation = this.generation;
        const stream = await this.mediaDevices.getUserMedia({
            audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true }, video: false,
        });
        if (generation !== this.generation) {
            stream.getTracks().forEach(track => track.stop());
            return false;
        }
        this.stream = stream;
        try {
            const context = new this.Context();
            this.context = context;
            await context.audioWorklet.addModule("/assets/recorder-worklet.js");
            if (generation !== this.generation) return false;
            this.rate = context.sampleRate;
            this.node = new AudioWorkletNode(context, "gpt-pi-recorder");
            let frames = 0;
            this.node.port.onmessage = ({ data }) => {
                if (generation !== this.generation) return;
                frames += data.length;
                if (frames <= this.rate * 30) this.chunks.push(data);
            };
            this.source = context.createMediaStreamSource(stream);
            this.source.connect(this.node);
            // A silent output keeps processing active in Chromium.
            this.node.connect(context.destination);
            await context.resume();
            if (generation !== this.generation) return false;
            this.timer = setTimeout(onLimit, 30000);
            stream.getAudioTracks().forEach(track => { track.onended = onEnded; });
            return true;
        } catch (error) {
            if (generation !== this.generation) return false;
            this.cancel(); throw error;
        }
    }
    finish() {
        const audio = pcmWave(this.chunks, this.rate || 16000);
        this.cancel();
        return audio;
    }
    cancel() {
        this.generation++;
        clearTimeout(this.timer);
        this.stream?.getTracks().forEach(track => { track.onended = null; track.stop(); });
        this.source?.disconnect();
        this.node?.disconnect();
        this.node?.port.close();
        this.context?.close().catch(() => {});
        this.stream = this.source = this.node = this.context = null;
        this.chunks = [];
    }
}
