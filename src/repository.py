"""Получение информации о пакетах из репозитория Ubuntu (apt).

Также содержит тестовый репозиторий, описанный текстовым файлом.

Менеджеры пакетов и сторонние библиотеки не используются: индексный файл
репозитория (Packages, Packages.gz или Packages.xz) скачивается и
разбирается средствами стандартной библиотеки Python.
"""
import gzip
import lzma
import re
import urllib.error
import urllib.request

TIMEOUT_SECONDS = 60
CONTINUATION_CHARS = " \t"
ALTERNATIVE_SEP = "|"
VERSION_START = "("
ARCH_SEP = ":"
TEST_NAME_RE = re.compile(r"^[A-Z]+$")


class RepositoryError(Exception):
    """Ошибка при получении или разборе данных репозитория."""


def fetch(url):
    """Скачивает файл по URL и возвращает его содержимое в байтах."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as resp:
            return resp.read()
    except urllib.error.HTTPError as error:
        raise RepositoryError(
            f"сервер вернул ошибку HTTP {error.code} для {url}") from None
    except urllib.error.URLError as error:
        raise RepositoryError(
            f"не удалось подключиться к {url}: {error.reason}") from None
    except OSError as error:
        raise RepositoryError(
            f"ошибка сети при загрузке {url}: {error}") from None


def decompress(data, url):
    """Распаковывает индекс по расширению файла (.gz, .xz)."""
    try:
        if url.endswith(".gz"):
            return gzip.decompress(data)
        if url.endswith(".xz"):
            return lzma.decompress(data)
    except (OSError, EOFError, lzma.LZMAError) as error:
        raise RepositoryError(
            f"не удалось распаковать индекс: {error}") from None
    return data


def download_index(url):
    """Скачивает индекс репозитория и возвращает его в виде текста."""
    data = decompress(fetch(url), url)
    return data.decode("utf-8", errors="replace")


def parse_packages(text):
    """Разбирает текст файла Packages на список словарей.

    Файл состоит из абзацев (по одному на пакет), разделённых пустой
    строкой. Строка абзаца имеет вид «Поле: значение»; строка,
    начинающаяся с пробела, продолжает предыдущее поле.
    """
    packages = []
    current = {}
    last_key = None
    for line in text.splitlines():
        if not line.strip():
            if current:
                packages.append(current)
            current, last_key = {}, None
        elif line[0] in CONTINUATION_CHARS:
            if last_key:
                current[last_key] += "\n" + line.strip()
        else:
            key, _, value = line.partition(":")
            last_key = key.strip()
            current[last_key] = value.strip()
    if current:
        packages.append(current)
    return packages


def parse_depends(field):
    """Возвращает список имён пакетов из значения поля Depends.

    Пример: "libc6 (>= 2.34), libssl3 | libssl1.1, perl:any"
    превращается в ["libc6", "libssl3", "perl"]: ограничения версий
    и квалификаторы архитектуры отбрасываются, из альтернатив берётся
    первая.
    """
    result = []
    for item in field.split(","):
        first = item.split(ALTERNATIVE_SEP)[0]
        name = first.split(VERSION_START)[0]
        name = name.split(ARCH_SEP)[0].strip()
        if name and name not in result:
            result.append(name)
    return result


class AptRepository:
    """Репозиторий Ubuntu, построенный по тексту индексного файла."""

    def __init__(self, text):
        """Строит словарь {имя пакета: список его абзацев}."""
        self.index = {}
        for stanza in parse_packages(text):
            name = stanza.get("Package")
            if name:
                self.index.setdefault(name, []).append(stanza)
        if not self.index:
            raise RepositoryError(
                "индекс репозитория пуст или имеет неверный формат")

    @classmethod
    def from_url(cls, url):
        """Скачивает индекс по URL и создаёт репозиторий."""
        return cls(download_index(url))

    def has_package(self, name):
        """Проверяет, есть ли пакет в репозитории."""
        return name in self.index

    def versions(self, name):
        """Возвращает список доступных версий пакета."""
        return [st.get("Version", "?") for st in self.index.get(name, [])]

    def find(self, name, version=None):
        """Возвращает абзац пакета заданной версии (или первый)."""
        stanzas = self.index.get(name, [])
        if version is None:
            return stanzas[0] if stanzas else None
        for stanza in stanzas:
            if stanza.get("Version") == version:
                return stanza
        return None

    def get_dependencies(self, name, version=None):
        """Возвращает прямые зависимости (поля Pre-Depends и Depends)."""
        stanza = self.find(name, version)
        if stanza is None:
            return []
        fields = stanza.get("Pre-Depends", "") + "," + \
            stanza.get("Depends", "")
        return parse_depends(fields)


class TestRepository:
    """Тестовый репозиторий: граф пакетов из текстового файла.

    Формат — одна строка на пакет: "A: B C" (A зависит от B и C).
    Имена пакетов — большие латинские буквы, # начинает комментарий.
    """

    def __init__(self, path):
        """Читает файл описания графа."""
        self.graph = {}
        try:
            with open(path, encoding="utf-8") as file:
                lines = file.readlines()
        except OSError as error:
            raise RepositoryError(
                f"не удалось прочитать файл {path}: {error}") from None
        for line_no, line in enumerate(lines, start=1):
            self._add_line(line.split("#")[0].strip(), f"{path}:{line_no}")

    def _add_line(self, line, place):
        """Разбирает одну строку описания графа."""
        if not line:
            return
        if ":" not in line:
            raise RepositoryError(f"{place}: ожидается 'ПАКЕТ: ЗАВИСИМОСТИ'")
        name, _, rest = line.partition(":")
        name, deps = name.strip(), rest.split()
        for pkg in [name] + deps:
            if not TEST_NAME_RE.match(pkg):
                raise RepositoryError(
                    f"{place}: имя '{pkg}' должно состоять "
                    "из больших латинских букв")
        if name in self.graph:
            raise RepositoryError(f"{place}: пакет '{name}' описан повторно")
        self.graph[name] = list(dict.fromkeys(deps))

    def has_package(self, name):
        """Проверяет, описан ли пакет в файле."""
        return name in self.graph

    def get_dependencies(self, name, version=None):
        """Возвращает зависимости пакета (версии в тесте не используются)."""
        return self.graph.get(name, [])
