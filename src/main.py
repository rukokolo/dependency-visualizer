"""Инструмент визуализации графа зависимостей пакетов Ubuntu (apt).

Этап 2: получение прямых зависимостей пакета из репозитория.
"""
import sys

from config import ConfigError, load_config
from repository import AptRepository, RepositoryError

DEFAULT_CONFIG = "config.csv"
EXIT_ERROR = 1


class AppError(Exception):
    """Ошибка, после которой приложение завершается."""


def get_config_path(args):
    """Возвращает путь к конфигурации из аргументов командной строки."""
    return args[0] if args else DEFAULT_CONFIG


def open_repository(cfg):
    """Загружает репозиторий и проверяет наличие пакета нужной версии."""
    if cfg["test_mode"]:
        raise AppError("тестовый режим будет реализован на этапе 3")
    print(f"Загрузка индекса репозитория: {cfg['repository']}")
    try:
        repo = AptRepository.from_url(cfg["repository"])
    except RepositoryError as error:
        raise AppError(f"репозиторий недоступен: {error}") from None
    name, version = cfg["package_name"], cfg["package_version"]
    if not repo.has_package(name):
        raise AppError(f"пакет '{name}' не найден в репозитории")
    if repo.find(name, version) is None:
        available = ", ".join(repo.versions(name))
        raise AppError(f"версия '{version}' пакета '{name}' не найдена. "
                       f"Доступные версии: {available}")
    return repo


def print_dependencies(name, version, deps):
    """Выводит прямые зависимости пакета."""
    print(f"Прямые зависимости пакета {name} {version} ({len(deps)}):")
    for dep in deps:
        print(f"  - {dep}")


def main():
    """Запускает приложение."""
    try:
        cfg = load_config(get_config_path(sys.argv[1:]))
        repo = open_repository(cfg)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    except AppError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    name, version = cfg["package_name"], cfg["package_version"]
    print_dependencies(name, version, repo.get_dependencies(name, version))


if __name__ == "__main__":
    main()
