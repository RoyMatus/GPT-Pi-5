import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
    FluentProvider,
    webLightTheme,
    webDarkTheme,
    Button,
    Badge,
    Avatar,
    Textarea,
    Select,
    Spinner,
    Switch,
    Dialog,
    DialogSurface,
    DialogBody,
    DialogTitle,
    DialogContent,
    DialogActions,
    MessageBar,
    MessageBarBody,
    Tooltip,
} from "@fluentui/react-components";
import {
    Add24Regular,
    Chat24Regular,
    Settings24Regular,
    LockClosed24Regular,
    ArrowUp24Regular,
    Stop24Filled,
    Sparkle24Regular,
    ShieldCheckmark24Regular,
    WeatherMoon24Regular,
    WeatherSunny24Regular,
    ArrowRight24Regular,
    Lightbulb24Regular,
    Edit24Regular,
    BookOpen24Regular,
    Dismiss24Regular,
} from "@fluentui/react-icons";
import "./style.css";

const errors = {
    connection:
        "Не удалось связаться с OpenAI. Проверь подключение и попробуй ещё раз.",
    login_failed:
        "Вход не завершён. Проверь подключение к OpenAI и повтори попытку.",
    invalid_login: "Не удалось подтвердить вход. Начни его заново.",
    login_expired: "Время на вход истекло. Попробуй ещё раз.",
    login_cancelled: "Вход отменён. Можно попробовать снова в любое время.",
    session_expired: "Сеанс завершён. Войди снова, чтобы продолжить.",
    plan_permission:
        "Аккаунт подключён без разрешения использовать подписку. Заверши сеанс и разреши использование плана при входе.",
    access_denied:
        "OpenAI не разрешил этот запрос. Проверь доступность сервиса для аккаунта и региона.",
    usage_limit:
        "Достигнут лимит подписки. Проверь использование в настройках ChatGPT.",
    incomplete: "Ответ оборвался до завершения. Он отмечен как незавершённый.",
    timeout: "Ответ занял слишком много времени. Запрос остановлен.",
    busy: "Дождись текущего ответа или останови его.",
    conversation_limit:
        "Этот разговор достиг лимита прототипа. Начни новый чат.",
    chat_limit:
        "Достигнут лимит 25 чатов в сеансе. Заверши сеанс, чтобы очистить их.",
    select_model: "Сначала выбери доступную модель.",
    response_limit: "Достигнут лимит длины ответа прототипа.",
    invalid_message: "Введи сообщение длиной до 8000 символов.",
    offline_mode:
        "Приложение запущено в автономном режиме. Вход сейчас отключён.",
};
const explain = (code) =>
    errors[code] || "Не удалось выполнить действие. Попробуй ещё раз.";

function App() {
    const [dark, setDark] = useState(
        () => localStorage.getItem("gpt-pi-theme") === "dark",
    );
    const [session, setSession] = useState(null);
    const [models, setModels] = useState([]);
    const [model, setModel] = useState("");
    const [chats, setChats] = useState([]);
    const [chatId, setChatId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [draft, setDraft] = useState("");
    const [busy, setBusy] = useState(false);
    const [signingIn, setSigningIn] = useState(false);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [registration, setRegistration] = useState("");
    const [notice, setNotice] = useState("");
    const [loading, setLoading] = useState(true);
    const abort = useRef(null);
    const epoch = useRef(0);
    const bottom = useRef(null);
    const sessionRef = useRef(null);
    const input = useRef(null);
    const authenticated = !!session?.authenticated;

    function clearPrivate() {
        epoch.current++;
        abort.current?.abort();
        setChats([]);
        setChatId(null);
        setMessages([]);
        setDraft("");
        setModels([]);
        setModel("");
        setBusy(false);
    }

    async function api(path, data, signal) {
        const options = { credentials: "same-origin", signal };
        if (data !== undefined)
            Object.assign(options, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRF-Token": sessionRef.current?.csrf || "",
                },
                body: JSON.stringify(data),
            });
        const response = await fetch(path, options);
        if (!response.ok) {
            const result = await response.json().catch(() => ({}));
            if (response.status === 401) {
                clearPrivate();
                sessionRef.current = null;
                setSession(null);
            }
            throw new Error(result.error || "connection");
        }
        return response;
    }

    async function bootstrap() {
        try {
            const fresh = await (await api("/api/session")).json();
            sessionRef.current = fresh;
            setSession(fresh);
            setRegistration(fresh.registrations?.[0]?.id || "");
            if (fresh.authenticated) {
                const mark = epoch.current;
                if (!fresh.account.sharing) {
                    setNotice(explain("plan_permission"));
                    return;
                }
                const available = await (await api("/api/models")).json();
                if (epoch.current !== mark) return;
                setModels(available.models);
                setModel(available.models[0]?.id || "");
                if (!available.models.length)
                    setNotice(
                        "Для этого подключения пока нет доступных моделей.",
                    );
                const saved = await (await api("/api/chats")).json();
                if (epoch.current !== mark) return;
                setChats(saved.chats);
                if (saved.chats.length) await openChat(saved.chats.at(-1).id);
            }
        } catch (error) {
            setNotice(explain(error.message));
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        const error = new URLSearchParams(location.search).get("error");
        if (error) setNotice(explain(error));
        history.replaceState(null, "", "/");
        bootstrap();
        const timer = setInterval(async () => {
            if (!sessionRef.current?.authenticated) return;
            try {
                const fresh = await (await fetch("/api/session")).json();
                if (!fresh.authenticated) {
                    clearPrivate();
                    sessionRef.current = fresh;
                    setSession(fresh);
                    setNotice(explain("session_expired"));
                }
            } catch {
                /* Polling must not turn a transient outage into a new identity. */
            }
        }, 10000);
        return () => {
            clearInterval(timer);
            abort.current?.abort();
        };
    }, []);
    useEffect(() => {
        bottom.current?.scrollIntoView({
            behavior: busy ? "instant" : "smooth",
        });
    }, [messages]);
    useEffect(() => {
        localStorage.setItem("gpt-pi-theme", dark ? "dark" : "light");
    }, [dark]);

    async function signIn() {
        setSigningIn(true);
        setNotice("");
        try {
            if (!sessionRef.current) {
                const fresh = await (await api("/api/session")).json();
                sessionRef.current = fresh;
                setSession(fresh);
            }
            const result = await (
                await api("/api/auth/start", {
                    registration: registration || null,
                })
            ).json();
            location.assign(result.url);
        } catch (error) {
            setNotice(explain(error.message));
            setSigningIn(false);
        }
    }

    async function signOut() {
        clearPrivate();
        setSettingsOpen(false);
        setNotice("");
        const old = sessionRef.current;
        sessionRef.current = old;
        setSession(null);
        try {
            const result = await (await api("/api/logout", {})).json();
            if (!result.revocation_confirmed)
                setNotice(
                    "Сеанс очищен на устройстве. Отзыв доступа в OpenAI не подтверждён; отключить приложение можно в настройках ChatGPT.",
                );
        } catch {
            setNotice(
                "Связь с устройством прервалась. Закрой окно; сервер завершит неактивный сеанс автоматически.",
            );
        } finally {
            sessionRef.current = null;
            setLoading(true);
            await bootstrap();
        }
    }

    async function openChat(id) {
        const mark = ++epoch.current;
        setNotice("");
        try {
            const chat = await (await api("/api/chats/" + id)).json();
            if (mark !== epoch.current) return;
            setChatId(id);
            setMessages(chat.messages);
            setDraft("");
        } catch (error) {
            setNotice(explain(error.message));
        }
    }

    function newChat() {
        if (busy) return;
        epoch.current++;
        setChatId(null);
        setMessages([]);
        setDraft("");
        setNotice("");
        input.current?.focus();
    }

    async function send(event) {
        event?.preventDefault();
        if (!draft.trim() || busy || !model || !authenticated) return;
        const text = draft.trim();
        const mark = ++epoch.current;
        const controller = new AbortController();
        abort.current = controller;
        setBusy(true);
        setNotice("");
        setDraft("");
        let id = chatId;
        try {
            if (!id) {
                const created = await (
                    await api("/api/chats", {}, controller.signal)
                ).json();
                if (mark !== epoch.current) return;
                id = created.id;
                setChatId(id);
                setChats((old) => [...old, { id, title: text.slice(0, 60) }]);
            }
            setMessages((old) => [
                ...old,
                { role: "user", content: text },
                { role: "assistant", content: "", incomplete: true },
            ]);
            const response = await api(
                "/api/chats/" + id + "/messages",
                { text, model },
                controller.signal,
            );
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            while (true) {
                const { value, done } = await reader.read();
                if (done || mark !== epoch.current) break;
                buffer += decoder.decode(value, { stream: true });
                const blocks = buffer.split("\n\n");
                buffer = blocks.pop();
                for (const block of blocks) {
                    if (!block.startsWith("data: ")) continue;
                    const data = JSON.parse(block.slice(6));
                    if (data.type === "delta" || data.type === "done")
                        setMessages((old) => {
                            const copy = [...old];
                            const last = { ...copy.at(-1) };
                            if (data.type === "delta")
                                last.content += data.text;
                            else last.incomplete = false;
                            copy[copy.length - 1] = last;
                            return copy;
                        });
                    if (data.type === "error") setNotice(explain(data.code));
                }
            }
        } catch (error) {
            if (mark === epoch.current && error.name !== "AbortError")
                setNotice(explain(error.message));
        } finally {
            if (mark === epoch.current) {
                setBusy(false);
                if (id) {
                    try {
                        const chat = await (
                            await api("/api/chats/" + id)
                        ).json();
                        if (mark === epoch.current) setMessages(chat.messages);
                    } catch {
                        /* Keep visible error and partial response. */
                    }
                }
            }
        }
    }

    async function stop() {
        try {
            await api("/api/cancel", {});
        } catch {
            abort.current?.abort();
        }
    }

    const prompts = [
        [
            Lightbulb24Regular,
            "Разобраться в сложном",
            "Объясни простыми словами, как работают нейросети.",
        ],
        [
            Edit24Regular,
            "Найти нужные слова",
            "Помоги написать короткое и понятное письмо. Сначала уточни адресата и цель.",
        ],
        [
            BookOpen24Regular,
            "Спланировать день",
            "Помоги составить реалистичный план на день. Сначала спроси о моих задачах.",
        ],
    ];

    return (
        <FluentProvider
            theme={dark ? webDarkTheme : webLightTheme}
            className={"app " + (dark ? "dark" : "")}
        >
            <aside className="sidebar">
                <div className="brand">
                    <div className="brand-mark">
                        <Sparkle24Regular />
                    </div>
                    <div>
                        <strong>
                            GPT-Pi <span>5</span>
                        </strong>
                        <small>Твоё пространство</small>
                    </div>
                </div>
                <Button
                    appearance="primary"
                    icon={<Add24Regular />}
                    size="large"
                    disabled={!authenticated || busy}
                    onClick={newChat}
                >
                    Новый чат
                </Button>
                <div className="nav-label">РАЗГОВОРЫ</div>
                <nav aria-label="Разговоры" className="chat-list">
                    {!chats.length && (
                        <div className="empty-list">
                            <Chat24Regular />
                            <p>
                                Здесь появятся
                                <br />
                                твои разговоры
                            </p>
                        </div>
                    )}
                    {[...chats].reverse().map((c) => (
                        <Button
                            key={c.id}
                            appearance={
                                c.id === chatId ? "secondary" : "subtle"
                            }
                            icon={<Chat24Regular />}
                            disabled={busy}
                            onClick={() => openChat(c.id)}
                        >
                            {c.title}
                        </Button>
                    ))}
                </nav>
                <div className="sidebar-bottom">
                    <div className="device">
                        <span className="status-dot" />
                        <div>
                            Личное устройство
                            <small>Чаты только в этом сеансе</small>
                        </div>
                    </div>
                    <Button
                        appearance="subtle"
                        icon={<Settings24Regular />}
                        onClick={() => setSettingsOpen(true)}
                    >
                        Настройки
                    </Button>
                    {authenticated && (
                        <Button
                            appearance="subtle"
                            icon={<LockClosed24Regular />}
                            onClick={signOut}
                        >
                            Завершить сеанс
                        </Button>
                    )}
                    <div className="profile">
                        <Avatar
                            name={session?.account?.name || "Гость"}
                            color="brand"
                            size={32}
                        />
                        <div>
                            <strong>{session?.account?.name || "Гость"}</strong>
                            <small>
                                {authenticated
                                    ? "Подключён к ChatGPT"
                                    : "Войди, чтобы начать"}
                            </small>
                        </div>
                    </div>
                </div>
            </aside>

            <main className="main">
                <header className="topbar">
                    <div className="topbar-title">
                        <Chat24Regular />
                        <span>Помощник</span>
                        <Badge appearance="tint" color="brand" size="small">
                            Прототип
                        </Badge>
                    </div>
                    <div className="topbar-actions">
                        {authenticated && (
                            <Select
                                aria-label="Модель ChatGPT"
                                value={model}
                                disabled={busy || !models.length}
                                onChange={(_, data) => setModel(data.value)}
                            >
                                {!models.length && (
                                    <option value="">
                                        Нет доступной модели
                                    </option>
                                )}
                                {models.map((m) => (
                                    <option key={m.id} value={m.id}>
                                        {m.name}
                                    </option>
                                ))}
                            </Select>
                        )}
                        <Tooltip
                            content={dark ? "Светлая тема" : "Тёмная тема"}
                            relationship="label"
                        >
                            <Button
                                appearance="subtle"
                                icon={
                                    dark ? (
                                        <WeatherSunny24Regular />
                                    ) : (
                                        <WeatherMoon24Regular />
                                    )
                                }
                                onClick={() => setDark(!dark)}
                            />
                        </Tooltip>
                    </div>
                </header>

                {notice && (
                    <div className="notice">
                        <MessageBar intent="warning">
                            <MessageBarBody>{notice}</MessageBarBody>
                            <Button
                                appearance="transparent"
                                aria-label="Закрыть уведомление"
                                icon={<Dismiss24Regular />}
                                onClick={() => setNotice("")}
                            />
                        </MessageBar>
                    </div>
                )}

                <div
                    className={
                        "content " + (messages.length ? "has-messages" : "")
                    }
                >
                    {loading ? (
                        <div className="loading">
                            <Spinner label="Готовим пространство…" />
                        </div>
                    ) : !authenticated ? (
                        <section className="welcome">
                            <div className="orb" aria-hidden="true">
                                <Sparkle24Regular />
                            </div>
                            <span className="eyebrow">
                                GPT-PI 5 · ЛИЧНЫЙ ПОМОЩНИК
                            </span>
                            <h1>
                                Хороший разговор
                                <br />
                                начинается здесь.
                            </h1>
                            <p className="welcome-copy">
                                Разбирайся в идеях, находи слова и строй планы.
                                <br />
                                Твой ChatGPT — на твоём устройстве.
                            </p>
                            <div className="signin-card">
                                <div className="signin-heading">
                                    <ShieldCheckmark24Regular />
                                    <div>
                                        <strong>Подключи свой ChatGPT</strong>
                                        <p>
                                            Вход через официальный сайт OpenAI
                                        </p>
                                    </div>
                                </div>
                                {!!session?.registrations?.length && (
                                    <Select
                                        aria-label="Сохранённое подключение"
                                        value={registration}
                                        onChange={(_, data) =>
                                            setRegistration(data.value)
                                        }
                                    >
                                        {session.registrations.map((r) => (
                                            <option key={r.id} value={r.id}>
                                                {r.name}
                                            </option>
                                        ))}
                                        <option value="">
                                            Другой аккаунт или рабочее
                                            пространство
                                        </option>
                                    </Select>
                                )}
                                <Button
                                    appearance="primary"
                                    size="large"
                                    icon={
                                        signingIn ? (
                                            <Spinner size="tiny" />
                                        ) : (
                                            <ArrowRight24Regular />
                                        )
                                    }
                                    iconPosition="after"
                                    onClick={signIn}
                                    disabled={
                                        signingIn ||
                                        session?.provider === "offline"
                                    }
                                >
                                    Continue with ChatGPT
                                </Button>
                                <p className="signin-note">
                                    Используются доступные лимиты твоей
                                    подписки.
                                    <br />
                                    Отдельный платный API не подключается.
                                </p>
                            </div>
                            <div className="privacy-line">
                                <LockClosed24Regular />
                                Пароль остаётся у OpenAI
                            </div>
                        </section>
                    ) : !messages.length ? (
                        <section className="chat-welcome">
                            <div className="mini-orb">
                                <Sparkle24Regular />
                            </div>
                            <span className="eyebrow">
                                ЕСТЬ О ЧЁМ ПОГОВОРИТЬ
                            </span>
                            <h1>С чего начнём?</h1>
                            <p>Задай вопрос или выбери идею для разговора.</p>
                            <div className="prompt-grid">
                                {prompts.map(([Icon, title, text]) => (
                                    <Button
                                        key={title}
                                        appearance="secondary"
                                        onClick={() => {
                                            setDraft(text);
                                            input.current?.focus();
                                        }}
                                    >
                                        <Icon />
                                        <strong>{title}</strong>
                                        <ArrowRight24Regular />
                                    </Button>
                                ))}
                            </div>
                        </section>
                    ) : (
                        <section
                            className="messages"
                            aria-label="Переписка"
                            aria-busy={busy}
                        >
                            {messages.map((m, i) => (
                                <article
                                    key={i}
                                    className={"message " + m.role}
                                >
                                    <Avatar
                                        name={
                                            m.role === "user"
                                                ? session?.account?.name
                                                : "GPT Pi"
                                        }
                                        icon={
                                            m.role === "assistant" ? (
                                                <Sparkle24Regular />
                                            ) : undefined
                                        }
                                        color={
                                            m.role === "assistant"
                                                ? "brand"
                                                : "neutral"
                                        }
                                        size={32}
                                    />
                                    <div className="message-body">
                                        <div className="message-author">
                                            {m.role === "user"
                                                ? "Ты"
                                                : "GPT-Pi 5"}
                                        </div>
                                        <div className="message-text">
                                            {m.content ||
                                                (busy &&
                                                i === messages.length - 1 ? (
                                                    <Spinner
                                                        size="tiny"
                                                        label="Думаю…"
                                                    />
                                                ) : (
                                                    "Ответ не получен."
                                                ))}
                                        </div>
                                        {m.incomplete && !busy && (
                                            <small className="incomplete">
                                                Незавершённый ответ
                                            </small>
                                        )}
                                    </div>
                                </article>
                            ))}
                            <div ref={bottom} />
                        </section>
                    )}
                </div>

                {authenticated && (
                    <div className="composer-area">
                        <form className="composer" onSubmit={send}>
                            <Textarea
                                ref={input}
                                aria-label="Сообщение"
                                placeholder="Спроси о том, что важно…"
                                value={draft}
                                resize="none"
                                appearance="outline"
                                maxLength={8000}
                                onChange={(_, data) => setDraft(data.value)}
                                onKeyDown={(e) => {
                                    if (
                                        e.key === "Enter" &&
                                        !e.shiftKey &&
                                        !e.nativeEvent.isComposing
                                    ) {
                                        e.preventDefault();
                                        send();
                                    }
                                }}
                            />
                            <div className="composer-bottom">
                                <span>
                                    <span className="status-dot" />
                                    Подписка ChatGPT
                                </span>
                                {busy ? (
                                    <Button
                                        appearance="secondary"
                                        icon={<Stop24Filled />}
                                        onClick={stop}
                                    >
                                        Остановить
                                    </Button>
                                ) : (
                                    <Button
                                        type="submit"
                                        appearance="primary"
                                        icon={<ArrowUp24Regular />}
                                        aria-label="Отправить сообщение"
                                        disabled={!draft.trim() || !model}
                                    />
                                )}
                            </div>
                        </form>
                        <p className="composer-note">
                            Ответы могут содержать ошибки. Чаты удалятся при
                            выходе из сеанса.
                        </p>
                    </div>
                )}
                <footer className="footer">
                    <span>Создано для твоего Raspberry Pi</span>
                    <span>Текстовый прототип · Микрофон выключен</span>
                </footer>
            </main>

            <Dialog
                open={settingsOpen}
                onOpenChange={(_, data) => setSettingsOpen(data.open)}
            >
                <DialogSurface>
                    <DialogBody>
                        <DialogTitle>Твоё пространство</DialogTitle>
                        <DialogContent>
                            <div className="settings-content">
                                <h3>Оформление</h3>
                                <Switch
                                    checked={dark}
                                    label="Тёмная тема"
                                    onChange={(_, data) =>
                                        setDark(data.checked)
                                    }
                                />
                                <h3>Подключение</h3>
                                <p>
                                    {authenticated
                                        ? "Используется твой план ChatGPT. Доступные модели определяет OpenAI."
                                        : "Войди через OpenAI, чтобы подключить свой план ChatGPT."}
                                </p>
                                <a
                                    href="https://chatgpt.com/#settings/Usage"
                                    target="_blank"
                                    rel="noreferrer"
                                >
                                    Управлять использованием в ChatGPT ↗
                                </a>
                                <h3>Приватность</h3>
                                <p>
                                    Разговоры и токены доступны только в текущем
                                    сеансе и не записываются на диск. После 30
                                    минут без запросов сеанс завершается.
                                </p>
                                <p>
                                    Это прототип для личного использования.
                                    Отдельные защищённые профили и голос ещё не
                                    реализованы. Завершение сеанса приложения не
                                    выходит из аккаунта на сайте OpenAI.
                                </p>
                                <small>Fluent 2 · GPT-Pi 5 v0.2</small>
                            </div>
                        </DialogContent>
                        <DialogActions>
                            <Button
                                appearance="primary"
                                onClick={() => setSettingsOpen(false)}
                            >
                                Готово
                            </Button>
                        </DialogActions>
                    </DialogBody>
                </DialogSurface>
            </Dialog>
        </FluentProvider>
    );
}

createRoot(document.getElementById("root")).render(<App />);
