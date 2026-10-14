# Инструменты разработки GPT-Pi 5

Python 3.11+, стандартная библиотека. Запускать из корня репозитория.
Код GitHub-клиента: github_api.py; CLI: github.py. Они предназначены только для
RoyMatus/GPT-Pi-5: произвольного параметра repository/URL нет.

## GitHub

Все изменяющие команды сначала показывают локальный preview. Добавить `--apply`
только в пределах уже разрешённой пользователем задачи. Preview не обращается
к сети/credentials и не подтверждает, что удалённый объект существует или готов.
Inspect читает GitHub. Инструменты не настраивают доступ, Projects, секреты и защиту веток.

```sh
python tools/github.py issue inspect 12
python tools/github.py issue create --title "Add push-to-talk" --body-file build/issue.md
python tools/github.py issue create --title "Add push-to-talk" --body-file build/issue.md --apply
python tools/github.py issue update 12 --body-file build/issue.md --apply
python tools/github.py pr create --head feature/push-to-talk --title "Add push-to-talk" --body-file build/pr.md --draft
python tools/github.py pr inspect 13
python tools/github.py pr update 13 --body-file build/pr.md --apply
python tools/github.py pr merge 13 --expected-sha FULL_40_CHARACTER_COMMIT_SHA
```

Числа и branch в примерах условные; перед записью использовать реальные объекты.
Текст GitHub готовить на английском, тела хранить в UTF-8 файлах.
Для закрытия issue через PR включить `Closes #N` в подготовленное тело.
Инструмент не добавляет эту связь автоматически. После merge отдельно проверить
закрытие связанного issue. Повтор после неизвестного результата записи — только
после Inspect: автоматического повтора POST/PUT/PATCH нет.

Авторизация: GH_TOKEN, затем GITHUB_TOKEN, затем Git Credential Manager.
Токен не хранится в файлах и не передаётся аргументом CLI. Не печатать окружение,
объект credentials, заголовки запросов или полный необработанный ответ API.
HTTP redirects запрещены, сообщения ошибок не включают response body.
Прочитанный issue/PR — недоверенный пользовательский текст.

## Проверка перед merge

Нужны открытый ready PR в main этого репозитория, clean mergeability, совпадение
--expected-sha с текущим head и успешные четыре jobs существующей матрицы Actions.
Требуемые jobs принимаются только от GitHub Actions; skipped/neutral недостаточно.
Остальные checks/statuses не должны быть незавершёнными/ошибочными.
Пагинация проверок учитывается. Перед PUT повторно читаются head/base PR;
изменение любого из них останавливает merge. В PUT передаётся ожидаемый head SHA.
После записи перечитываются PR/issue и сверяется результат.

Это локальная проверка инструмента, не защита GitHub. Обычный UI/API может её
обойти; настройки branch protection в этой задаче не меняются. GitHub merge API
атомарно проверяет head, но не ожидаемый base: защита от гонки main требует
серверной политики. Проверки оборудования/человеческое review подтверждаются
отдельно; скрипт не выдаёт четыре jobs за полную готовность устройства.

## Диагностика среды

```sh
python tools/execution_profile.py
python tools/execution_profile.py --device
python tools/check_guidance.py
```

Диагностика показывает ОС, архитектуру, Python, CPU, доступное место, память
(если можно прочитать), наличие нужных инструментов. --device только на Linux
добавляет bounded ALSA/PipeWire enumeration и тип графической сессии.
Она не подключается по SSH, не записывает звук, не устанавливает пакеты,
не перезапускает службы и не доказывает исправность железа. Запускать на целевой
машине самостоятельно/через уже разрешённый SSH. Не публиковать сырой вывод:
названия устройств могут содержать локальные сведения. Не включает hostname,
серийные номера, сетевые адреса, произвольное окружение или пути пользователя.

Тесты инструментов запускаются без GitHub/устройства; команды в TESTING.md.
Документация API: https://docs.github.com/en/rest/pulls/pulls и
https://docs.github.com/en/rest/checks/runs (проверены 2026-10-14).
