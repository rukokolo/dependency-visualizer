"""Загрузка и проверка конфигурации из CSV-файла.

Формат файла: две колонки «ключ,значение». Первая строка может быть
заголовком "key,value", строки, начинающиеся с #, пропускаются.
"""
import csv
import os
import re
from urllib.parse import urlparse

COLUMNS_COUNT = 2
MIN_DEPTH = 1
HEADER = ("key", "value")
TRUE_VALUES = ("true", "1", "yes")
FALSE_VALUES = ("false", "0", "no")
URL_SCHEMES = ("http", "https")

PARAMS = {
    "package_name": "Имя анализируемого пакета",
    "repository": "URL репозитория или путь к файлу тестового репозитория",
    "test_mode": "Режим работы с тестовым репозиторием (true/false)",
    "package_version": "Версия пакета",
    "ascii_tree": "Режим вывода зависимостей в виде ASCII-дерева",
    "max_depth": "Максимальная глубина анализа зависимостей",
    "filter_substring": "Подстрока для фильтрации пакетов",
}

REAL_PACKAGE_RE = re.compile(r"^[a-z0-9][a-z0-9+.\-]+$")
TEST_PACKAGE_RE = re.compile(r"^[A-Z]+$")


class ConfigError(Exception):
    """Ошибка в конфигурационном файле."""


def is_skipped(row):
    """Проверяет, что строку CSV нужно пропустить.

    Пропускаются пустые строки, комментарии (#) и заголовок key,value.
    """
    cells = [cell.strip() for cell in row]
    if not any(cells):
        return True
    if cells[0].startswith("#"):
        return True
    return tuple(cell.lower() for cell in cells) == HEADER


def add_param(raw, row, line_no):
    """Добавляет пару ключ-значение из строки CSV в словарь raw."""
    if len(row) != COLUMNS_COUNT:
        raise ConfigError(
            f"строка {line_no}: ожидается 2 столбца (ключ,значение), "
            f"получено {len(row)}")
    key, value = row[0].strip(), row[1].strip()
    if key not in PARAMS:
        raise ConfigError(f"строка {line_no}: неизвестный параметр '{key}'")
    if key in raw:
        raise ConfigError(
            f"строка {line_no}: параметр '{key}' задан повторно")
    raw[key] = value


def read_csv(path):
    """Читает CSV-файл и возвращает словарь {ключ: строковое значение}."""
    if not os.path.isfile(path):
        raise ConfigError(f"файл конфигурации не найден: {path}")
    raw = {}
    with open(path, encoding="utf-8-sig", newline="") as file:
        for line_no, row in enumerate(csv.reader(file), start=1):
            if not is_skipped(row):
                add_param(raw, row, line_no)
    missing = [key for key in PARAMS if key not in raw]
    if missing:
        raise ConfigError("не заданы параметры: " + ", ".join(missing))
    return raw


def parse_bool(key, value):
    """Преобразует строку true/false в логическое значение."""
    lowered = value.lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    raise ConfigError(
        f"параметр '{key}': ожидается true или false, получено '{value}'")


def check_package_name(name, test_mode):
    """Проверяет имя пакета и возвращает его.

    В обычном режиме имя состоит из a-z, 0-9, '+', '-', '.'
    (правило Debian Policy), в тестовом — из больших латинских букв.
    """
    if not name:
        raise ConfigError("параметр 'package_name': имя не может быть пустым")
    if test_mode and not TEST_PACKAGE_RE.match(name):
        raise ConfigError(
            "параметр 'package_name': в тестовом режиме имя состоит "
            f"из больших латинских букв, получено '{name}'")
    if not test_mode and not REAL_PACKAGE_RE.match(name):
        raise ConfigError(
            f"параметр 'package_name': недопустимое имя пакета '{name}' "
            "(разрешены a-z, 0-9, '+', '-', '.')")
    return name


def check_repository(repo, test_mode):
    """Проверяет URL репозитория или путь к тестовому файлу."""
    if not repo:
        raise ConfigError(
            "параметр 'repository': значение не может быть пустым")
    if test_mode:
        if not os.path.isfile(repo):
            raise ConfigError(
                "параметр 'repository': файл тестового репозитория "
                f"не найден: {repo}")
        return repo
    parsed = urlparse(repo)
    if parsed.scheme not in URL_SCHEMES or not parsed.netloc:
        raise ConfigError(
            "параметр 'repository': ожидается URL вида http(s)://..., "
            f"получено '{repo}'")
    return repo


def check_version(version, test_mode):
    """Проверяет версию пакета (в тестовом режиме версии не используются)."""
    if test_mode:
        return version
    if not version:
        raise ConfigError(
            "параметр 'package_version': версия не может быть пустой")
    if " " in version:
        raise ConfigError(
            "параметр 'package_version': версия не может содержать "
            f"пробелы, получено '{version}'")
    return version


def parse_depth(value):
    """Преобразует максимальную глубину в целое число >= MIN_DEPTH."""
    try:
        depth = int(value)
    except ValueError:
        raise ConfigError(
            "параметр 'max_depth': ожидается целое число, "
            f"получено '{value}'") from None
    if depth < MIN_DEPTH:
        raise ConfigError(
            f"параметр 'max_depth': глубина должна быть >= {MIN_DEPTH}, "
            f"получено {depth}")
    return depth


def load_config(path):
    """Читает конфигурацию, проверяет все параметры и возвращает словарь
    со значениями нужных типов (str, bool, int)."""
    raw = read_csv(path)
    test_mode = parse_bool("test_mode", raw["test_mode"])
    return {
        "package_name": check_package_name(raw["package_name"], test_mode),
        "repository": check_repository(raw["repository"], test_mode),
        "test_mode": test_mode,
        "package_version": check_version(raw["package_version"], test_mode),
        "ascii_tree": parse_bool("ascii_tree", raw["ascii_tree"]),
        "max_depth": parse_depth(raw["max_depth"]),
        "filter_substring": raw["filter_substring"],
    }
