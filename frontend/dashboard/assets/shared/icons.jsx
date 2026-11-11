// Official exports verified against @fluentui/react-icons 2.0.345.
// Reuse the existing package; do not replace these with emoji or rasterized glyphs.
import {
  Home24Regular, Desktop24Regular, DataBarVertical24Regular,
  CalendarLtr24Regular, Image24Regular, Sparkle24Regular,
  Settings24Regular, DeveloperBoard24Regular, Memory16Regular,
  HardDrive24Regular, Wifi124Regular, ArrowDownload24Regular,
  ArrowUpload24Regular, Gift24Regular, ChevronLeft24Regular,
  ChevronRight24Regular, Add24Regular, Mic24Regular, MicOff24Regular,
  Send24Regular, Keyboard24Regular, CheckmarkCircle24Regular,
  History24Regular, DocumentText24Regular, Play24Regular,
  Pause24Regular, Dismiss24Regular, WeatherPartlyCloudyDay24Regular,
} from "@fluentui/react-icons";

export const dashboardIcons = Object.freeze({
  overview: Home24Regular, computer: Desktop24Regular,
  markets: DataBarVertical24Regular, calendar: CalendarLtr24Regular,
  photos: Image24Regular, assistant: Sparkle24Regular,
  settings: Settings24Regular, cpu: DeveloperBoard24Regular,
  gpu: DeveloperBoard24Regular, memory: Memory16Regular,
  disk: HardDrive24Regular, network: Wifi124Regular,
  download: ArrowDownload24Regular, upload: ArrowUpload24Regular,
  gift: Gift24Regular, previous: ChevronLeft24Regular,
  next: ChevronRight24Regular, add: Add24Regular,
  microphone: Mic24Regular, microphoneOff: MicOff24Regular,
  send: Send24Regular, keyboard: Keyboard24Regular,
  healthy: CheckmarkCircle24Regular, history: History24Regular,
  document: DocumentText24Regular, play: Play24Regular,
  pause: Pause24Regular, close: Dismiss24Regular,
  partlyCloudy: WeatherPartlyCloudyDay24Regular,
});

export const dashboardTabs = Object.freeze([
  { id: "overview", label: "Обзор", icon: dashboardIcons.overview },
  { id: "computer", label: "Компьютер", icon: dashboardIcons.computer },
  { id: "markets", label: "Рынки", icon: dashboardIcons.markets },
  { id: "calendar", label: "Календарь", icon: dashboardIcons.calendar },
  { id: "photos", label: "Фото", icon: dashboardIcons.photos },
  { id: "assistant", label: "Ассистент", icon: dashboardIcons.assistant },
]);
