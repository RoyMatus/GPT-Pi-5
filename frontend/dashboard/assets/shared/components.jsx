import React, { useId } from "react";
import { Button, FluentProvider, Textarea, webDarkTheme } from "@fluentui/react-components";
import { dashboardIcons as Icon, dashboardTabs } from "./icons.jsx";
import "./tokens.css";

// Presentational primitives only. Consumers own data, actions, lifecycle and access.
export const dashboardTheme = {
  ...webDarkTheme,
  fontFamilyBase: '"Segoe UI Variable", "Segoe UI", system-ui, sans-serif',
  colorNeutralBackground1: "#111922", colorNeutralBackground2: "#1b2530",
  colorNeutralBackground3: "#242e39", colorNeutralForeground1: "#f6f7fb",
  colorNeutralForeground2: "#bdc8d6", colorNeutralStroke1: "#43505e",
  colorBrandBackground: "#0079be", colorBrandBackgroundHover: "#0b8ed4",
  colorBrandForeground1: "#63d8ff",
};

export function DashboardProvider({ children, className = "", style }) {
  return <FluentProvider theme={dashboardTheme} className={`dashboard ${className}`} style={style}>{children}</FluentProvider>;
}

export function DashboardNavigation({ activeTab, onNavigate }) {
  return <nav className="dashboard-nav" aria-label="Разделы приложения">
    {dashboardTabs.map(({ id, label, icon: TabIcon }) => <Button
      key={id} className="dashboard-nav-item" appearance="transparent"
      aria-current={activeTab === id ? "page" : undefined}
      onClick={() => onNavigate(id)}>
      <TabIcon aria-hidden="true" /><span>{label}</span>
    </Button>)}
  </nav>;
}

export function DashboardFrame({ title, activeTab, onNavigate, onSettings, connected = false,
  connectionLabel = "ПК не подключён", footer, fullscreen = false, children }) {

  return <div className={`dashboard-shell ${fullscreen ? "dashboard-fullscreen" : ""}`}>
    {!fullscreen && <header className="dashboard-header"><h1>{title}</h1>
      <div className="dashboard-header-status"><span className="dashboard-status-dot" data-connected={connected} aria-hidden="true" />
        <span>{connectionLabel}</span>
        {onSettings && <Button className="dashboard-icon-button" appearance="transparent" icon={<Icon.settings />} aria-label="Настройки" onClick={onSettings} />}
      </div>
    </header>}
    <main className="dashboard-content" aria-label={title}>{children}</main>
    {!fullscreen && onNavigate && <DashboardNavigation activeTab={activeTab} onNavigate={onNavigate} />}
    {!fullscreen && footer && <div className="dashboard-footer">{footer}</div>}
  </div>;
}

export function Panel({ title, icon: PanelIcon, actions, className = "", children }) {
  return <section className={`dashboard-panel ${className}`}>
    {title && <h2 className="dashboard-panel-title">{PanelIcon && <PanelIcon aria-hidden="true" />}<span>{title}</span>
      {actions && <span className="dashboard-panel-actions">{actions}</span>}</h2>}
    {children}
  </section>;
}

export function MetricCard({ label, value, detail, icon: MetricIcon, children, className = "" }) {
  return <section className={`dashboard-panel ${className}`} aria-label={label}>
    <div className="dashboard-metric-heading">{MetricIcon && <MetricIcon aria-hidden="true" />}<span>{label}</span></div>
    <div className="dashboard-row dashboard-between"><strong className="dashboard-metric-value">{value ?? "—"}</strong>
      {detail && <span className="dashboard-metric-detail">{detail}</span>}</div>
    {children}
  </section>;
}

export function ProgressMeter({ value, label }) {
  if (!Number.isFinite(value)) return <div className="dashboard-empty">Нет данных</div>;
  const bounded = Math.max(0, Math.min(100, value));
  return <div className="dashboard-progress" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={bounded}>
    <div className="dashboard-progress-fill" style={{ width: `${bounded}%` }} />
  </div>;
}

// Input samples are already normalized by a screen adapter; this is not telemetry.
export function Sparkline({ values, label, tone = "blue", min, max, large = false }) {
  const id = useId().replaceAll(":", "");
  if (!Array.isArray(values) || values.length < 2 || values.some(v => !Number.isFinite(v))) {
    return <div className="dashboard-empty">График недоступен</div>;
  }
  const lo = min ?? Math.min(...values); const hi = max ?? Math.max(...values);
  const span = Math.max(hi - lo, 1);
  const points = values.map((v, i) => [i * 300 / (values.length - 1), 57 - Math.max(0, Math.min(1, (v - lo) / span)) * 54]);
  const line = points.map(([x, y], i) => `${i ? "L" : "M"}${x},${y}`).join(" ");
  return <svg className={`dashboard-sparkline ${large ? "dashboard-graph" : ""}`} data-tone={tone}
    viewBox="0 0 300 60" preserveAspectRatio="none" role="img" aria-label={label}>
    <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop stopColor="currentColor" stopOpacity=".25" /><stop offset="1" stopColor="currentColor" stopOpacity=".02" /></linearGradient></defs>
    <path d={`${line} L300,60 L0,60 Z`} fill={`url(#${id})`} />
    <path d={line} fill="none" stroke="currentColor" strokeWidth="2" vectorEffect="non-scaling-stroke" />
  </svg>;
}

export function ClockHero({ time, dateLabel, artwork, artworkAlt = "", children }) {
  return <div className="dashboard-hero"><div><div className="dashboard-clock">{time}</div><div className="dashboard-hero-date">{dateLabel}</div></div>
    {artwork ? <img className="dashboard-seasonal-art" src={artwork} alt={artworkAlt} /> : children}
  </div>;
}

export function CountdownCard({ title, countLabel, dateLabel }) {
  return <section className="dashboard-panel dashboard-countdown" aria-label={title}><Icon.gift aria-hidden="true" />
    <div><div className="dashboard-countdown-label">{title}</div><div className="dashboard-countdown-value">{countLabel}</div><div className="dashboard-secondary">{dateLabel}</div></div>
  </section>;
}

// Cells are supplied by calendar logic: { key, day, dateTime, selected, today, hasEvent } or null.
// No local timezone, recurrence, persistence or date arithmetic is implemented here.
export function MonthCalendar({ monthLabel, cells, onPrevious, onNext, onToday, onSelect }) {
  const padded = [...cells]; while (padded.length % 7) padded.push(null);
  return <section className="dashboard-panel">
    <div className="dashboard-calendar-heading">
      {onPrevious && <Button className="dashboard-icon-button" appearance="transparent" icon={<Icon.previous />} aria-label="Предыдущий месяц" onClick={onPrevious} />}
      <h2>{monthLabel}</h2>
      {onNext && <Button className="dashboard-icon-button" appearance="transparent" icon={<Icon.next />} aria-label="Следующий месяц" onClick={onNext} />}
      {onToday && <Button onClick={onToday}>Сегодня</Button>}
    </div>
    <div className="dashboard-calendar-scroll"><table className="dashboard-calendar" aria-label={monthLabel}><thead><tr>{["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map(d => <th key={d} scope="col">{d}</th>)}</tr></thead>
      <tbody>{Array.from({ length: padded.length / 7 }, (_, r) => <tr key={r}>{padded.slice(r * 7, r * 7 + 7).map((cell, c) => <td key={cell?.key ?? c}>
        {cell && (onSelect ? <Button appearance="transparent" className="dashboard-calendar-day" data-selected={Boolean(cell.selected)} aria-pressed={Boolean(cell.selected)} aria-current={cell.today ? "date" : undefined}
          aria-label={`${cell.dateTime}${cell.hasEvent ? ", есть событие" : ""}`} onClick={() => onSelect(cell)}>{cell.day}{cell.hasEvent && <span className="dashboard-event-dot" />}</Button>
          : <time dateTime={cell.dateTime} className="dashboard-calendar-day" data-selected={Boolean(cell.selected)} aria-current={cell.today ? "date" : undefined}>{cell.day}{cell.hasEvent && <span className="dashboard-event-dot" />}</time>)}
      </td>)}</tr>)}</tbody>
    </table></div>
  </section>;
}

export function Agenda({ entries, onAdd }) {
  return <Panel title="Ближайшие события" icon={Icon.calendar} actions={onAdd && <Button className="dashboard-icon-button" appearance="transparent" icon={<Icon.add />} aria-label="Добавить событие" onClick={onAdd} />}>
    {entries.length ? entries.map(entry => <div className="dashboard-agenda-row" key={entry.id}><strong>{entry.dateLabel}</strong><span>{entry.title}</span></div>) : <div className="dashboard-secondary">Нет ближайших событий</div>}
  </Panel>;
}

export function Suggestion({ icon: SuggestionIcon, children, onChoose }) {
  return <Button className="dashboard-suggestion" onClick={onChoose}>{SuggestionIcon && <SuggestionIcon aria-hidden="true" />}<span>{children}</span><Icon.next className="dashboard-suggestion-tail" aria-hidden="true" /></Button>;
}

export function Composer({ value, onChange, onSend, onMicrophone, onKeyboard, recording = false, busy = false }) {
  return <div className="dashboard-composer"><div className="dashboard-panel">
    <Textarea className="dashboard-composer-input" appearance="outline" value={value} onChange={(_, data) => onChange(data.value)} placeholder="Спросите что-нибудь…" aria-label="Сообщение ассистенту" />
    <div className="dashboard-composer-actions">
      {onMicrophone && <Button className="dashboard-icon-button" icon={<Icon.microphone />} aria-pressed={recording} aria-label={recording ? "Остановить запись" : "Начать запись"} onClick={onMicrophone} />}
      {onKeyboard && <Button className="dashboard-icon-button" icon={<Icon.keyboard />} aria-label="Клавиатура" onClick={onKeyboard} />}
      {onSend && <Button appearance="primary" className="dashboard-icon-button" icon={<Icon.send />} aria-label="Отправить" disabled={!value.trim() || busy} onClick={onSend} />}
    </div>
  </div><div className="dashboard-microphone-state" role="status">{recording ? <Icon.microphone /> : <Icon.microphoneOff />}{recording ? "Идёт запись" : "Микрофон выключен"}</div></div>;
}

// External playback logic supplies src, controlsVisible and callbacks. No timer or filesystem access.
export function PhotoFrame({ src, alt, fit = "cover", onReveal, controlsVisible = false, controls, onImageError }) {
  return <div className="dashboard-photo"><img src={src} alt={alt} style={{ objectFit: fit }} onError={onImageError} />
    {onReveal && <button className="dashboard-photo-reveal" aria-label="Показать управление фотографиями" onClick={onReveal} />}
    {controlsVisible && <div className="dashboard-photo-controls">{controls}</div>}
  </div>;
}
