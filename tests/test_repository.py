"""Тесты получения зависимостей из репозитория (этап 2)."""
import gzip
import os
import pathlib
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from repository import (  # noqa: E402
    AptRepository, RepositoryError, download_index, parse_depends,
    parse_packages)

SAMPLE = os.path.join(ROOT, "tests", "data", "Packages")


def read_sample():
    """Возвращает текст тестового индекса."""
    with open(SAMPLE, encoding="utf-8") as file:
        return file.read()


class ParseTest(unittest.TestCase):
    """Проверка разбора файла Packages и поля Depends."""

    def test_parse_packages(self):
        """Абзацы разделяются, продолжения строк приклеиваются."""
        packages = parse_packages(read_sample())
        self.assertEqual(len(packages), 4)
        self.assertEqual(packages[0]["Package"], "curl")
        self.assertIn("curl is", packages[0]["Description"])

    def test_parse_depends(self):
        """Версии, альтернативы и :any отбрасываются, повторов нет."""
        field = "libc6 (>= 2.34), libssl3 | libssl1.1, perl:any, libc6"
        self.assertEqual(parse_depends(field), ["libc6", "libssl3", "perl"])

    def test_parse_depends_empty(self):
        """Пустое поле даёт пустой список."""
        self.assertEqual(parse_depends(""), [])


class AptRepositoryTest(unittest.TestCase):
    """Проверка класса AptRepository на тестовом индексе."""

    def setUp(self):
        """Создаёт репозиторий из тестового индекса."""
        self.repo = AptRepository(read_sample())

    def test_direct_dependencies(self):
        """Прямые зависимости curl заданной версии."""
        deps = self.repo.get_dependencies("curl", "7.81.0-1")
        self.assertEqual(deps, ["libc6", "libcurl4", "zlib1g"])

    def test_pre_depends(self):
        """Pre-Depends учитываются вместе с Depends."""
        deps = self.repo.get_dependencies("libcurl4", "7.81.0-1")
        self.assertEqual(deps, ["libc6", "libssl3", "perl"])

    def test_version_choice(self):
        """Зависимости берутся для указанной версии пакета."""
        self.assertEqual(self.repo.get_dependencies("libc6", "2.36-0ubuntu1"),
                         ["libgcc-s1", "libcrypt1"])
        self.assertEqual(self.repo.versions("libc6"),
                         ["2.35-0ubuntu3", "2.36-0ubuntu1"])

    def test_missing_package_and_version(self):
        """Отсутствующий пакет или версия не находятся."""
        self.assertFalse(self.repo.has_package("nosuchpkg"))
        self.assertIsNone(self.repo.find("curl", "1.0"))

    def test_empty_index(self):
        """Пустой индекс даёт RepositoryError."""
        with self.assertRaises(RepositoryError):
            AptRepository("")


class DownloadTest(unittest.TestCase):
    """Проверка загрузки и распаковки индекса (file:// вместо сети)."""

    def test_gzip_index(self):
        """Сжатый gzip индекс скачивается и распаковывается."""
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp, "Packages.gz")
            path.write_bytes(gzip.compress(read_sample().encode()))
            text = download_index(path.as_uri())
        self.assertIn("Package: curl", text)

    def test_missing_file(self):
        """Несуществующий адрес даёт RepositoryError."""
        missing = pathlib.Path(ROOT, "tests", "data", "nope.gz").as_uri()
        with self.assertRaises(RepositoryError):
            download_index(missing)


if __name__ == "__main__":
    unittest.main()
