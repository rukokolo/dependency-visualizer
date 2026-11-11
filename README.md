# Dependency Graph Visualizer

Инструмент визуализации графа зависимостей для менеджера пакетов Ubuntu (apt)
(вариант 7).

## Общее описание

CLI-приложение на Python, которое строит граф зависимостей пакета Ubuntu.
Готовые менеджеры пакетов и сторонние библиотеки для получения зависимостей
не используются. Все параметры задаются в конфигурационном файле формата CSV.

## Этап 1: Минимальный прототип с конфигурацией

- Параметры читаются из конфигурационного файла CSV (`ключ,значение`)
- При запуске выводятся все параметры в формате ключ-значение
  (только на этапе 1)
- Каждый параметр проверяется, при ошибке выводится понятное сообщение
  и программа завершается с кодом 1

## Этап 2: Сбор данных

- Используется формат пакетов Ubuntu (apt); менеджеры пакетов
  и сторонние библиотеки не используются
- Индекс репозитория (`Packages`, `Packages.gz` или `Packages.xz`)
  скачивается по URL и разбирается вручную (модули `urllib`, `gzip`, `lzma`)
- Зависимости берутся для заданной пользователем версии пакета
  (поля `Pre-Depends` и `Depends`)
- Ограничения версий `(>= x)` и квалификаторы `:any` отбрасываются,
  из альтернатив `a | b` берётся первая
- На экран выводятся прямые зависимости пакета
- Обработка ошибок: нет соединения, ошибка HTTP, повреждённый архив,
  пустой индекс, пакет не найден, версия не найдена
  (выводится список доступных версий)

## Настройки

Конфигурационный файл — CSV из двух столбцов. Первая строка `key,value` —
заголовок, строки, начинающиеся с `#`, — комментарии.

| Параметр | Описание | Допустимые значения |
|---|---|---|
| `package_name` | имя анализируемого пакета | `a-z 0-9 + - .`; в тестовом режиме — `A-Z` |
| `repository` | URL репозитория или путь к файлу тестового репозитория | `http(s)://...`; в тестовом режиме — существующий файл |
| `test_mode` | режим работы с тестовым репозиторием | `true` / `false` |
| `package_version` | версия пакета | непустая строка без пробелов (в тестовом режиме не проверяется) |
| `ascii_tree` | режим вывода зависимостей в формате ASCII-дерева | `true` / `false` |
| `max_depth` | максимальная глубина анализа зависимостей | целое число >= 1 |
| `filter_substring` | подстрока для фильтрации пакетов | любая строка, пустая — без фильтра |

Обрабатываемые ошибки: файл не найден, неверное число столбцов, неизвестный,
повторный или пропущенный параметр, а также неверное значение любого параметра.

## Функции

`src/main.py` — точка входа:

- `get_config_path(args)` — путь к конфигурации из аргументов
  (по умолчанию `config.csv`)
- `open_repository(cfg)` — загрузка репозитория и проверка наличия
  пакета нужной версии
- `print_dependencies(name, version, deps)` — вывод прямых зависимостей
- `main()` — запуск приложения и обработка ошибок
- `AppError` — исключение для ошибок, завершающих приложение

`src/config.py` — чтение и проверка конфигурации:

- `read_csv(path)` — чтение CSV в словарь строк
- `is_skipped(row)` — пропуск пустых строк, комментариев и заголовка
- `add_param(raw, row, line_no)` — проверка строки и добавление параметра
- `parse_bool(key, value)` — преобразование `true/false`
- `check_package_name(name, test_mode)` — проверка имени пакета
- `check_repository(repo, test_mode)` — проверка URL или пути к файлу
- `check_version(version, test_mode)` — проверка версии
- `parse_depth(value)` — проверка максимальной глубины
- `load_config(path)` — чтение и проверка всей конфигурации
- `ConfigError` — исключение для ошибок конфигурации

`src/repository.py` — получение данных из репозитория:

- `fetch(url)` — скачивание файла по URL
- `decompress(data, url)` — распаковка `.gz` / `.xz`
- `download_index(url)` — скачивание и распаковка индекса в текст
- `parse_packages(text)` — разбор индекса на абзацы «поле: значение»
- `parse_depends(field)` — извлечение имён пакетов из поля `Depends`
- `AptRepository` — репозиторий: `from_url(url)` (загрузка),
  `has_package(name)`, `versions(name)`, `find(name, version)`,
  `get_dependencies(name, version)`
- `RepositoryError` — исключение для ошибок репозитория

## Структура проекта

```
src/            исходный код
tests/          тесты
tests/configs/  конфигурации с ошибками
tests/data/     тестовый индекс репозитория Packages
config.csv      пример конфигурации
run.bat         запуск в Windows
run.sh          запуск в Linux/macOS
```

## Сборка и запуск

Сборка не требуется, нужен Python 3.8+ без сторонних библиотек.

```
run.bat config.csv
./run.sh config.csv
python src/main.py config.csv
```

Если путь к конфигурации не указан, используется `config.csv`.

## Запуск тестов

```
python -m unittest discover -s tests -v
```

- `tests/test_config.py` — чтение и проверка конфигурации
- `tests/test_repository.py` — разбор индекса и поля `Depends`, выбор
  версии, `Pre-Depends`, распаковка gzip; сеть в тестах не используется

## Примеры использования

### Этап 1: корректная конфигурация

```
key,value
package_name,curl
repository,http://archive.ubuntu.com/ubuntu/dists/jammy/main/binary-amd64/Packages.gz
test_mode,false
package_version,7.81.0-1
ascii_tree,true
max_depth,3
filter_substring,
```

```
> run.bat config.csv
Параметры конфигурации:
  package_name = 'curl'
  repository = 'http://archive.ubuntu.com/ubuntu/dists/jammy/main/binary-amd64/Packages.gz'
  test_mode = False
  package_version = '7.81.0-1'
  ascii_tree = True
  max_depth = 3
  filter_substring = ''
```

### Этап 1: конфигурация с ошибкой

```
> run.bat tests/configs/bad_depth.csv
Ошибка конфигурации: параметр 'max_depth': глубина должна быть >= 1, получено -2
> run.bat tests/configs/bad_url.csv
Ошибка конфигурации: параметр 'repository': ожидается URL вида http(s)://..., получено 'ftp//не-url'
> run.bat tests/configs/bad_missing.csv
Ошибка конфигурации: не заданы параметры: max_depth
```

### Этап 2: прямые зависимости пакета

```
> run.bat config.csv
Загрузка индекса репозитория: http://archive.ubuntu.com/ubuntu/dists/jammy/main/binary-amd64/Packages.gz
Прямые зависимости пакета curl 7.81.0-1 (3):
  - libc6
  - libcurl4
  - zlib1g
```

### Этап 2: ошибки получения данных

```
> run.bat tests/configs/bad_version_not_found.csv
Ошибка: версия '1.0' пакета 'curl' не найдена. Доступные версии: 7.81.0-1
> run.bat tests/configs/bad_package_not_found.csv
Ошибка: пакет 'nosuchpkg' не найден в репозитории
> run.bat tests/configs/bad_repo_404.csv
Ошибка: репозиторий недоступен: сервер вернул ошибку HTTP 404 для http://archive.ubuntu.com/ubuntu/dists/jammy/main/binary-amd64/Nope.gz
```
