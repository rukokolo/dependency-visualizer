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
- На экран выводятся прямые зависимости пакета (только на этапе 2)
- Обработка ошибок: нет соединения, ошибка HTTP, повреждённый архив,
  пустой индекс, пакет не найден, версия не найдена
  (выводится список доступных версий)

## Этап 3: Основные операции

- Граф зависимостей с учётом транзитивности строится алгоритмом DFS
  с рекурсией
- Анализ ограничен максимальной глубиной (корень — глубина 0,
  его прямые зависимости — глубина 1)
- Пакеты, имя которых содержит подстроку фильтра, не учитываются
- Циклические зависимости обнаруживаются и выводятся, обход при этом
  не зацикливается
- Режим тестирования: вместо URL задаётся путь к файлу описания графа,
  пакеты в нём называются большими латинскими буквами

Формат файла тестового репозитория — одна строка на пакет:

```
# комментарий
A: B C      # A зависит от B и C
B: D
D:          # D ни от чего не зависит
```

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

Пример (`config.csv`):

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

Пример для тестового режима (`tests/configs/repo_simple.csv`):

```
key,value
package_name,A
repository,tests/repos/simple.txt
test_mode,true
package_version,
ascii_tree,false
max_depth,10
filter_substring,
```

Обрабатываемые ошибки: файл не найден, неверное число столбцов, неизвестный,
повторный или пропущенный параметр, а также неверное значение любого параметра.

## Функции

`src/main.py` — точка входа:

- `get_config_path(args)` — путь к конфигурации из аргументов
  (по умолчанию `config.csv`)
- `load_repository(cfg)` — открытие тестового или загрузка настоящего
  репозитория
- `check_package(repo, cfg)` — проверка наличия пакета нужной версии
- `make_get_deps(repo, cfg)` — функция получения прямых зависимостей
  (версия из конфигурации используется для корневого пакета)
- `run(cfg)` — построение и вывод графа
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
- `TestRepository` — тестовый репозиторий из файла описания графа:
  `has_package(name)`, `get_dependencies(name)`
- `RepositoryError` — исключение для ошибок репозитория

`src/graph.py` — граф зависимостей, класс `DependencyGraph`:

- `build(root)` — построение графа от корневого пакета
- `_visit(pkg, depth)` — рекурсивный обход в глубину (DFS)
- `_already_visited(pkg, depth)` — пропуск пакетов, уже обработанных
  на той же или меньшей глубине
- `is_filtered(name)` — проверка фильтра по подстроке
- `_add_cycle(dep)` — запоминание найденного цикла
- `format_lines()` — текстовое представление графа
- атрибуты: `edges` (список смежности), `cycles` (циклы),
  `truncated` (не раскрытые из-за глубины пакеты)

## Структура проекта

```
src/            исходный код
tests/          тесты
tests/configs/  конфигурации с ошибками
tests/data/     тестовый индекс репозитория Packages
tests/repos/    файлы тестовых репозиториев (графы из букв A-Z)
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
- `tests/test_graph.py` — тестовый репозиторий, транзитивность, циклы,
  ограничение глубины, фильтр

## Примеры использования

### Тестовый репозиторий: простой граф

`tests/repos/simple.txt`:

```
A: B C
B: D
C: D E
D:
E: F
F:
```

```
> run.bat tests/configs/repo_simple.csv
Граф зависимостей, пакетов: 6
  A -> B, C
  B -> D
  D -> (нет зависимостей)
  C -> D, E
  E -> F
  F -> (нет зависимостей)
Циклических зависимостей нет.
```

### Тестовый репозиторий: циклы

```
> run.bat tests/configs/repo_cycle.csv
Граф зависимостей, пакетов: 4
  A -> B
  B -> C
  C -> A, D
  D -> (нет зависимостей)
Цикл: A -> B -> C -> A
> run.bat tests/configs/repo_self_cycle.csv
Граф зависимостей, пакетов: 3
  A -> A, B
  B -> C
  C -> B
Цикл: A -> A
Цикл: B -> C -> B
```

### Тестовый репозиторий: глубина и фильтр

```
> run.bat tests/configs/repo_depth.csv          (max_depth = 3)
Граф зависимостей, пакетов: 4
  A -> B
  B -> C
  C -> D
  D -> (не раскрыт: достигнута максимальная глубина)
Циклических зависимостей нет.
> run.bat tests/configs/repo_filter.csv         (filter_substring = D)
Граф зависимостей, пакетов: 5
  A -> B, C
  B -> (нет зависимостей)
  C -> E
  E -> F
  F -> (нет зависимостей)
Циклических зависимостей нет.
```

### Реальный репозиторий Ubuntu

```
> run.bat tests/configs/real_nano.csv           (nano 6.2-1, max_depth = 3)
Загрузка индекса репозитория: http://archive.ubuntu.com/ubuntu/dists/jammy/main/binary-amd64/Packages.gz
Граф зависимостей, пакетов: 7
  nano -> libc6, libncursesw6, libtinfo6
  libc6 -> libgcc-s1, libcrypt1
  libgcc-s1 -> gcc-12-base, libc6
  gcc-12-base -> (не раскрыт: достигнута максимальная глубина)
  libcrypt1 -> libc6
  libncursesw6 -> libtinfo6, libc6
  libtinfo6 -> libc6
Цикл: libc6 -> libgcc-s1 -> libc6
Цикл: libc6 -> libcrypt1 -> libc6
> run.bat tests/configs/real_nano_filter.csv    (filter_substring = gcc)
Загрузка индекса репозитория: http://archive.ubuntu.com/ubuntu/dists/jammy/main/binary-amd64/Packages.gz
Граф зависимостей, пакетов: 5
  nano -> libc6, libncursesw6, libtinfo6
  libc6 -> libcrypt1
  libcrypt1 -> libc6
  libncursesw6 -> libtinfo6, libc6
  libtinfo6 -> libc6
Цикл: libc6 -> libcrypt1 -> libc6
```

### Ошибки

```
> run.bat tests/configs/bad_depth.csv
Ошибка конфигурации: параметр 'max_depth': глубина должна быть >= 1, получено -2
> run.bat tests/configs/bad_url.csv
Ошибка конфигурации: параметр 'repository': ожидается URL вида http(s)://..., получено 'ftp//не-url'
> run.bat tests/configs/bad_version_not_found.csv
Ошибка: версия '1.0' пакета 'curl' не найдена. Доступные версии: 7.81.0-1
> run.bat tests/configs/bad_package_not_found.csv
Ошибка: пакет 'nosuchpkg' не найден в репозитории
> run.bat tests/configs/repo_bad_format.csv
Ошибка: проблема с репозиторием: tests/repos/bad_format.txt:2: имя 'c' должно состоять из больших латинских букв
```
