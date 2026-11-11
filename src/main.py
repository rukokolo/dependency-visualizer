"""Инструмент визуализации графа зависимостей пакетов Ubuntu (apt).

Этап 3: построение графа зависимостей (DFS с рекурсией, глубина,
фильтр, циклы, тестовый режим).
"""
import sys

from config import ConfigError, load_config
from graph import DependencyGraph
from repository import AptRepository, RepositoryError, TestRepository

DEFAULT_CONFIG = "config.csv"
EXIT_ERROR = 1


class AppError(Exception):
    """Ошибка, после которой приложение завершается."""


def get_config_path(args):
    """Возвращает путь к конфигурации из аргументов командной строки."""
    return args[0] if args else DEFAULT_CONFIG


def load_repository(cfg):
    """Открывает тестовый репозиторий или скачивает настоящий."""
    try:
        if cfg["test_mode"]:
            return TestRepository(cfg["repository"])
        print(f"Загрузка индекса репозитория: {cfg['repository']}")
        return AptRepository.from_url(cfg["repository"])
    except RepositoryError as error:
        raise AppError(f"проблема с репозиторием: {error}") from None


def check_package(repo, cfg):
    """Проверяет, что пакет (и его версия) есть в репозитории."""
    name, version = cfg["package_name"], cfg["package_version"]
    if not repo.has_package(name):
        raise AppError(f"пакет '{name}' не найден в репозитории")
    if not cfg["test_mode"] and repo.find(name, version) is None:
        available = ", ".join(repo.versions(name))
        raise AppError(f"версия '{version}' пакета '{name}' не найдена. "
                       f"Доступные версии: {available}")


def make_get_deps(repo, cfg):
    """Создаёт функцию получения прямых зависимостей пакета.

    Версию пользователь задаёт только для корневого пакета, для
    остальных берётся версия, имеющаяся в репозитории.
    """
    root, version = cfg["package_name"], cfg["package_version"]

    def get_deps(name):
        """Возвращает прямые зависимости пакета name."""
        if name == root and not cfg["test_mode"]:
            return repo.get_dependencies(name, version)
        return repo.get_dependencies(name)

    return get_deps


def run(cfg):
    """Строит граф зависимостей и выводит его на экран."""
    repo = load_repository(cfg)
    check_package(repo, cfg)
    graph = DependencyGraph(make_get_deps(repo, cfg), cfg["max_depth"],
                            cfg["filter_substring"])
    graph.build(cfg["package_name"])
    print("\n".join(graph.format_lines()))


def main():
    """Запускает приложение."""
    try:
        run(load_config(get_config_path(sys.argv[1:])))
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    except AppError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    main()
