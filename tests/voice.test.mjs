import test from "node:test";
import assert from "node:assert/strict";
import { Microphone, pcmWave } from "../frontend/voice.js";

test("PCM is mono 16kHz, clipped and limited to 30 seconds", async () => {
    const input = new Float32Array(48000 * 31).fill(2);
    const view = new DataView(await pcmWave([input], 48000).arrayBuffer());
    assert.equal(view.getUint16(22, true), 1);
    assert.equal(view.getUint32(24, true), 16000);
    assert.equal(view.getUint32(40, true), 480000 * 2);
    assert.equal(view.getInt16(44, true), 32767);
});

test("permission arriving after cancel cannot open the microphone", async () => {
    let grant;
    let stopped = 0;
    const microphone = new Microphone({
        mediaDevices: { getUserMedia: () => new Promise(resolve => { grant = resolve; }) },
        Context: class { constructor() { throw new Error("must not open audio"); } },
    });
    const pending = microphone.start(() => {}, () => {});
    microphone.cancel();
    grant({ getTracks: () => [{ stop: () => stopped++ }] });
    assert.equal(await pending, false);
    assert.equal(stopped, 1);
});
