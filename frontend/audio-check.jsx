import React, { useEffect, useRef, useState } from "react";
import { Button, Dialog, DialogSurface, DialogBody, DialogTitle, DialogContent, DialogActions } from "@fluentui/react-components";
import { Mic24Regular, Speaker224Regular, Stop24Filled } from "@fluentui/react-icons";
import { Microphone, testSignal } from "./voice.js";

export function AudioCheck({ onClose }) {
    const [devices, setDevices] = useState({ microphone: null, speaker: null });
    const [state, setState] = useState("idle");
    const [message, setMessage] = useState("Нажми кнопку для проверки. Запись остаётся только в памяти этого окна.");
    const [level, setLevel] = useState(0);
    const [hasRecording, setHasRecording] = useState(false);
    const recorder = useRef(null);
    const audio = useRef(null);
    const recording = useRef(null);
    const generation = useRef(0);
    const alive = useRef(true);
    const playbackTimer = useRef(null);

    function stop() {
        generation.current++;
        clearTimeout(playbackTimer.current);
        recorder.current?.cancel();
        if (audio.current) {
            audio.current.onended = audio.current.onerror = null;
            audio.current.pause();
            URL.revokeObjectURL(audio.current.src);
            audio.current.removeAttribute("src");
            audio.current.load();
            audio.current = null;
        }
        if (alive.current) { setState("idle"); setLevel(0); }
    }
    function clear() {
        stop();
        recording.current = null;
        if (alive.current) setHasRecording(false);
    }
    async function refresh() {
        try {
            const response = await fetch('/api/audio/devices', { signal: AbortSignal.timeout(4000) });
            if (!response.ok) return;
            const fresh = await response.json();
            if (alive.current) setDevices(fresh);
            if (alive.current && audio.current && fresh.speaker === false) {
                stop(); setMessage("Динамик не найден системой. Воспроизведение остановлено.");
            }
            return fresh;
        } catch {
            return null;
        }
    }
    useEffect(() => {
        refresh();
        const timer = setInterval(refresh, 3000);
        const hide = () => {
            if (document.hidden) { clear(); setMessage("Проверка остановлена, запись удалена."); }
        };
        const leave = () => clear();
        document.addEventListener("visibilitychange", hide);
        window.addEventListener("pagehide", leave);
        return () => {
            alive.current = false; clear();
            clearInterval(timer);
            document.removeEventListener("visibilitychange", hide);
            window.removeEventListener("pagehide", leave);
        };
    }, []);

    function fail(error) {
        clear();
        setMessage({
            NotFoundError: "Микрофон не найден системой.",
            NotAllowedError: "Доступ к микрофону или динамику запрещён браузером.",
            NotReadableError: "Микрофон занят или отключён.",
        }[error.name] || "Не удалось выполнить проверку звука.");
    }
    function finish() {
        recording.current = recorder.current.finish();
        setHasRecording(true); setState("idle"); setLevel(0);
        setMessage("Запись готова. Нажми «Прослушать запись».");
    }
    async function record() {
        clear();
        const mark = generation.current;
        setState("permission"); setMessage("Подключаю микрофон…");
        try {
            recorder.current ||= new Microphone();
            const started = await recorder.current.start(finish,
                () => { clear(); refresh(); setMessage("Микрофон отключён. Проверка остановлена."); },
                { duration: 5000, onLevel: setLevel });
            if (started && mark === generation.current && alive.current) {
                setState("recording"); setMessage("Идёт запись · 5 секунд"); refresh();
            }
        } catch (error) { if (mark === generation.current && alive.current) fail(error); }
    }
    async function play(blob, label) {
        stop();
        const mark = generation.current;
        setState("checking"); setMessage("Проверяю аудиовыход…");
        const status = await refresh();
        if (mark !== generation.current || !alive.current || document.hidden) return;
        if (status?.speaker === false) {
            setState("idle"); setMessage("Динамик не найден системой. Тестовый сигнал не запущен."); return;
        }
        const player = new Audio(URL.createObjectURL(blob));
        audio.current = player;
        player.volume = .65;
        setState("playing"); setMessage(label);
        try {
            player.onended = () => { stop(); setMessage("Браузер завершил воспроизведение. Слышимость проверь на устройстве."); };
            player.onerror = () => { stop(); setMessage("Не удалось воспроизвести звук."); };
            playbackTimer.current = setTimeout(() => {
                stop(); setMessage("Воспроизведение не завершилось. Проверь аудиовыход устройства.");
            }, 8000);
            await player.play();
        } catch (error) { if (mark === generation.current && alive.current) fail(error); }
    }
    const name = kind => devices[kind] === false ? "Не обнаружен системой"
        : devices[kind] === true ? "Обнаружен системой" : "Системный выбор · нажми кнопку для проверки";
    return <Dialog open onOpenChange={(_, data) => { if (!data.open) onClose(); }}>
        <DialogSurface aria-label="Микрофон и динамик">
            <DialogBody>
                <DialogTitle>Микрофон и динамик</DialogTitle>
                <DialogContent className="audio-check">
                    <p>Используются системные микрофон и динамик. Номер USB-A порта Pi не фиксируется; подключение проверяется заново.</p>
                    <div className="audio-device"><strong>Микрофон</strong><span>{name("microphone")}</span></div>
                    <Button appearance="primary" icon={<Mic24Regular />} disabled={state !== "idle"} onClick={record}>Проверить микрофон</Button>
                    <meter aria-label="Уровень микрофона" min="0" max="1" value={level} />
                    <div className="audio-device"><strong>Динамик</strong><span>{name("speaker")}</span></div>
                    <Button icon={<Speaker224Regular />} disabled={state !== "idle"} onClick={() => play(testSignal(), "Воспроизвожу тестовый сигнал…")}>Проверить динамик</Button>
                    {hasRecording && <Button disabled={state !== "idle"} onClick={() => play(recording.current, "Воспроизвожу запись…")}>Прослушать запись</Button>}
                    {state !== "idle" && <Button icon={<Stop24Filled />} onClick={() => { clear(); setMessage("Проверка остановлена, запись удалена."); }}>Остановить проверку</Button>}
                    <p role="status" className={state === "recording" ? "recording-label" : ""}>{message}</p>
                    <small>Микрофон включается только по нажатию. Закрытие окна удаляет тестовую запись. Для динамика прозвучат два коротких сигнала.</small>
                </DialogContent>
                <DialogActions><Button onClick={onClose}>Закрыть проверку</Button></DialogActions>
            </DialogBody>
        </DialogSurface>
    </Dialog>;
}
