# Контекст для следующей ИИ-сессии

Обновлено: 2026-11-11.

## Цель и текущий прототип

GPT-Pi 5 — личное настольное устройство с сенсорным экраном и планируемым голосом.
Реализован текстовый прототип v0.2: Fluent 2 (официальный Fluent UI React v9),
OAuth/PKCE Sign in with ChatGPT, проверка ID token, модели из каталога аккаунта,
Responses streaming, отмена, завершение и истечение сеанса, ошибки доступа/квот.
Платный API и инструменты не подключены. Добавлен локальный русский голос:
запись по кнопке до 30 секунд, Vosk → редактируемый текст → план ChatGPT → Piper.
Аудио только в RAM, отмена/выход прекращают обработку и воспроизведение.
Движки установлены отдельно в data-dir/voice; реальное USB-аудио ещё не проверено.
2026-11-10 подтверждены реальный
вход владельца на Pi, получение моделей и ответ GPT-6.1-Sol через подключённый
план ChatGPT. Это не общая проверка доступности аккаунтов или регионов.

Чаты живут только в RAM. По умолчанию вход сохраняется на личном устройстве:
токены в backend data-dir/credentials, файлы 0600 и каталог 0700 на Linux,
атомарная замена при refresh, блокировка второго процесса с тем же data-dir.
Постоянная HttpOnly/SameSite cookie восстанавливает только свой сеанс, с проверкой
client ID и хеша subject регистрации. CSRF/Origin/Host-проверки сохраняются.
Перезапуск и 30 минут бездействия больше не завершают сохранённый вход;
временная ошибка refresh не удаляет доступ. Logout удаляет запись и пытается отозвать токен.
GPT_PI_REMEMBER_LOGIN=0 возвращает прежний RAM-only режим с idle timeout.
Метаданные регистрации и секреты хранятся в пользовательском каталоге, переписка — нет.
Это личный прототип, не реализация отдельных защищённых локальных пользователей.
Браузерная сессия OpenAI — отдельная сущность; kiosk использует постоянный отдельный профиль.

## Устройство и развёртывание

На разрешённом владельцем Pi обнаружены Debian 13 / ARM64, Python 3.13.5,
около 2 GB RAM, labwc/Wayland, Chromium, вертикальный DSI-экран 720×1280,
экранная клавиатура squeekboard. ALSA/PipeWire не показали микрофон;
активный выход PipeWire — Dummy Output. Это не тест качества аудио.

Прототип установлен в пользовательский каталог релизов; служба gpt-pi
работает от обычного пользователя на loopback. Создан автозапуск kiosk; после перезагрузки устройства проверены работа службы и экран входа.
Launcher v0.3.1 запускает Chromium kiosk на весь экран с text-input-v3.
Пользовательский GTK-модуль поднимает только OSK над fullscreen; оболочка учитывает
её высоту. Единственную squeekboard запускает графическая сессия через wrapper.
При каждом запуске включается пользовательская настройка автоматического показа.
На реальном Pi проверены автоматическое появление, ввод экранной буквы `q`
и скрытие при потере фокуса (синтетическая страница, автоматизированный указатель).
Установщик и откат описаны в deploy/README.md. Адреса, пароль и идентификаторы
устройства не записывать в Git. Нельзя выдавать настройку автозапуска за
проверку физического отключения питания.

## Проверки

Первоначальные 54 offline-теста установленного wheel на Windows/Python 3.12 и Debian 13 ARM64/Python 3.13: подпись/issuer/audience/nonce/expiry,
согласие на план, refresh, stream completion, CSRF, чужие ID, logout cancellation,
истечение и перезапуск. Браузер: светлая/тёмная тема, desktop/portrait/mobile,
настоящая кнопка начала OAuth; тестовый вход → модель → чат → отмена → выход.
Автономные проверки используют синтетические ответы; отдельный платный API не вызывается.
Ручная проверка с разрешения владельца дополнительно подтвердила реальный ответ
через план ChatGPT. Обнаруженный 403 после OAuth исправлен: cross-site GET корневого
document разрешён, API/iframe/POST и неверный Host остаются закрыты (два новых теста).
Артефакты текущей проверки находятся в игнорируемом build/ui/.
Итог развёртывания/устройства уточнять по deploy/README.md и текущим проверкам.

## Следующие задачи

- Шесть вкладок панели реализованы и объединены через PR #11–#17 в
  codex/dashboard-integration. v0.3.0 сохраняет вход/чат/голос, добавляет общую
  навигацию, SSH-телеметрию, рынки, календарь RAM, SFTP-фото и обзор/погоду.
  103 offline Python-теста, 7 Node-тестов и синтетические браузерные сценарии
  проходят. Реальный ПК не подменяется Pi; на текущем Windows нет sshd и
  процесс разработки не имеет административных прав для его установки.
  Папка фото требует отдельно проверенных серверных SFTP-ограничений.
  Физический тач/аудио и реальная библиотека не подтверждаются CI.
  Установка/фактические проверки устройства записываются в deploy/README.md.
- Проверить длительное использование и восстановление после потери сети/истечения токена.
- Проверить удобство физического касания пальцем и холодную загрузку.
- Отдельно спроектировать постоянное хранилище, локальные профили и шифрование.
- Проверить точность/задержку локального голоса с реальной речью; OAuth-план не поддерживает аудиовход.
- Подключить ReSpeaker XVF3800 с XIAO ESP32S3 как USB-аудио и проверить физический звук.
- Лицензия, допустимость общего использования персональной подписки, региональная
  доступность и бюджет дополнительных API остаются отдельными решениями.

Не сохранять секреты, сетевые реквизиты, настоящие разговоры и персональные данные.

## Локальный голос: проверено 2026-11-10

Выбраны Vosk 0.3.45/small-ru-0.22 и Piper 1.8.0/ru_RU-denis-medium.
На Pi синтетическая фраза прошла синтез (3,02 с) и распознавание (1,83 с) без
ошибок текста; изолированный рабочий процесс приложения также проверен.
Браузер с синтетическим микрофоном прошёл запись, показ текста, отправку,
озвучивание и выход во время записи. Новые тесты проверяют отмену, лимиты,
доступ по сеансу и позднее разрешение микрофона. Это не проверка живой речи.
По карточкам владельца оборудование — ReSpeaker XVF3800 с XIAO ESP32S3 и
динамик 4 Ом/5 Вт. На момент проверки USB-устройство не перечисляется даже
после сообщённого владельцем входа в Safe Mode и замены кабеля; прошивка не менялась.
Через USB XIAO и с другим устройством в соседнем порту также нет enumeration.
Проверка энергосбережения и переинициализация xHCI не помогли; причина USB не установлена.
Позднее новая контрольная флешка обнаружилась как USB Mass Storage (Sony M2 Card Reader,
480 Мбит/с). Поэтому общее отсутствие USB-устройств больше не является текущим
состоянием: использованный порт Pi работает. ReSpeaker всё ещё не обнаружен,
в том числе после обычной перезагрузки; нужны проверка в подтверждённом рабочем
порту Pi и Safe Mode на XMOS USB-C. Содержимое флешки не читалось.
Владелец позднее уточнил: красный индикатор горит постоянно, а не мигает;
Safe Mode не подтверждён. По просьбе владельца дальнейшая работа переключена
на кнопки в приложении, дополнительные переподключения сейчас не запрашивать.
Добавлена доступная без входа проверка микрофона/динамика, запись пяти секунд,
уровень сигнала и воспроизведение записи только из RAM. Номера USB-портов/ID
не закрепляются; используется текущий системный выбор. Список аудиоустройств
читается на Pi через pw-dump и отдаётся только как два признака доступности.
Browser enumerateDevices вызывал лишний запрос камеры в Chromium/Wayland;
он удалён, камера не нужна. Dummy Output не считается подключённым динамиком.
Исправленная проверка установлена на Pi: обе кнопки нажаты через настоящий
интерфейс без запроса камеры. Результат — микрофон и динамик не найдены системой;
тестовый сигнал при отсутствии выхода не запускается. На Windows прошли 23
Python-теста аудио/HTTP, три Node-теста и браузерный сценарий с синтетическим звуком.

## Сохранение входа: проверено 2026-11-10

Исправлен выход через 30 минут, при restart и при временной ошибке refresh.
75 offline-тестов прошли на Windows; 37 тестов облака, HTTP, сохранения входа
и аудио — на установленном wheel Debian ARM64. Chromium с синтетическим аккаунтом
проверил час простоя без ожидания, restart backend и браузера, явный выход;
голосовой браузерный сценарий также прошёл. Обновление установлено на Pi.
Постоянное окно заменило приватное; официальный экран OpenAI требует одного входа
в новом профиле. Восстановление реального аккаунта после этого изменения ещё
не подтверждено. Пароли/токены из браузера не извлекались.
Голосовой интерфейс установлен на Pi; шесть голосовых и 13 HTTP-тестов установленного
wheel прошли. CI коммита df40542 (Windows/Linux, Python 3.11/3.13, Node) успешен.

Dashboard foundation increment: /?dashboard exposes the supplied shell and system clock; / retains Assistant. Feature integrations and #10 acceptance remain outstanding. See docs/dashboard/FOUNDATION.md.

Assistant integration (#8): one mounted auth/chat controller inside the shell; inactive-tab voice and generation cancel, late results are discarded. Synthetic voice/tab transitions and remembered-login browser scenarios passed. No physical audio acceptance.

Computer #4: backend SSH profile/trust service, generated separate Ed25519 keys, Linux and Windows fixed collectors, bounded history and independent SFTP grant interface implemented. Public keys only reach UI. Real Linux ARM64/Windows collector schema verified; selected-PC SSH server/ACL setup is separate and no source is auto-selected.
Markets #5: fixed public read-only adapters (Kraken OHLC, MOEX ISS delayed candles, CBR XML FX), session watchlist and shared cache. Missing/stale/rate-limit states are explicit. Commodity provider is unsupported. Synthetic tests do not call live providers.
Calendar #6 implemented: Monday-first month navigation, separate today/selection/event markers, RAM session-owned event CRUD and calendar-day countdown. No external sync or private persistence. Synthetic API/IDOR and browser CRUD checks passed.

Photos #7 implemented: separate session grant using shared SSH/SFTP service, bounded one-folder listing, opaque image IDs, readonly path/link checks and limited metadata-free previews. Fullscreen controls/Escape and cleanup verified synthetically. Real PC folder and server confinement remain an actual setup/acceptance requirement.
Overview #3: real Open-Meteo forecast with explicit default/locality selection and attribution; consumes Computer/Markets source hooks without duplicate polling. Shared in-flight session reads prevent competing guest cookies on dashboard boot. Browser fixtures now block unrelated dashboard source requests, including voice-tab-transition tests.


2026-11-11, эпик #2: v0.3.0 установлена на Pi. 101 тест установленного приложения
прошёл на ARM64; 103 теста и 192 браузерных случая — локально. Chromium зависал
на заблокированном keyring; выделенный профиль переведён на file store (cookie
без шифрования keyring, права 0700). Все шесть вкладок открыты на реальном экране,
перезапуск backend проверен. При последующей настройке v0.3.1 действующий вход владельца подтверждён.
Реальный внешний ПК/SFTP-папка и физическое касание/аудио остаются воротами приёмки.


v0.3.1: по прямому запросу владельца добавлен fullscreen и отдельный установщик
Windows OpenSSH для фиксированного коллектора. Профиль источника настроен через
действующий авторизованный сеанс, ключи backend; адреса/секреты в Git не внесены.
Статус реальной установки SSH проверять отдельно: Windows требует UAC, preview
и подготовленные файлы не доказывают, что служба установлена или метрики получены.



v0.3.2 установлена на Pi. Windows SSH работает с отдельной стандартной учёткой,
ключом backend и закреплённым ключом сервера. Проверены реальные CPU/RAM/диск,
network counters/rates и отображение в Компьютере/Обзоре. Native kernel/.NET API
заменяют CIM, поскольку в SSH воспроизведён timeout даже Win32_Processor. Частота
CPU/температуры/GPU на этапе v0.3.2 недоступны; CPU usage на >64 logical CPU не выдаётся
за всю машину. Учётка не администратор, временная группа счётчиков удалена;
firewall — только Pi, широкое правило отключено. PTY, SFTP, forwarding и произвольные
команды запрещены и проверены реальным соединением. Приватный ключ хоста остался
только в защищённой системной папке; временная копия build удалена после проверки.
Вход приложения и fullscreen 720×1280 сохранены. Windows-служба automatic;
перезагрузка самого Windows-ПК не выполнялась. Фотокаталог/SFTP и физическое
касание/аудио остаются отдельной приёмкой.

v0.3.3: реализованы GPU NVIDIA (nvidia-smi) и отдельная явная установка CPU-датчиков
LHM 0.9.6 / подписанный PawnIO 2.2.0. На разрешённом Windows-ПК установлены датчики;
через реальное закреплённое SSH-соединение с Pi получены все семь полей CPU clock/
temperature, GPU load/temperature/VRAM used/total/power. Повторные публикации
исправлены для PowerShell 5.1 ([NullString]::Value в File.Replace); offline-регрессия
воспроизводила ошибку до исправления. CPU читает фиксированная задача SYSTEM
без исполняемых параметров и периодических триггеров; SSH-роль имеет read/run,
не admin и не прямой доступ к драйверу. Проверки PTY/SFTP/forwarding/forced-command
повторены успешно. Вентилятор RPM не поддержан; GPU относится к первой NVIDIA.
Пакет v0.3.3 установлен на Pi; в авторизованном Chromium проверены все семь новых
значений и их отображение в Компьютере/Обзоре, fullscreen 720×1280. После проверки
kiosk перезапущен с прежним профилем без порта отладки. Windows-ПК не перезагружался.

#19 / v0.3.4: 15 themes integrated; strict Windows comparison matches 165/165 originals. Owner-approved Pi typography uses installed Cantarell/Noto Sans Mono with adjusted metrics. See docs/theme-integration-19.md for checks, deployment and limitations.
