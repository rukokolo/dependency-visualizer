"""Инструмент визуализации графа зависимостей пакетов Ubuntu (apt).

Этап 1: минимальный прототип с конфигурацией.
"""
import sys

from config import PARAMS, ConfigError, load_config

DEFAULT_CONFIG = "config.csv"
EXIT_ERROR = 1


def get_config_path(args):
    """Возвращает путь к конфигурации из аргументов командной строки."""
    return args[0] if args else DEFAULT_CONFIG


def print_params(cfg):
    """Выводит все параметры конфигурации в формате ключ-значение."""
    print("Параметры конфигурации:")
    for key in PARAMS:
        print(f"  {key} = {cfg[key]!r}")


def main():
    """Запускает приложение."""
    try:
        cfg = load_config(get_config_path(sys.argv[1:]))
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    print_params(cfg)


if __name__ == "__main__":
    main()
