"""Тесты построения графа зависимостей (этап 3)."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from graph import DependencyGraph  # noqa: E402
from repository import RepositoryError, TestRepository  # noqa: E402

REPOS = os.path.join(ROOT, "tests", "repos")
NO_LIMIT = 100


def build(repo_name, max_depth=NO_LIMIT, filter_substring="", root="A"):
    """Строит граф по тестовому репозиторию из tests/repos."""
    repo = TestRepository(os.path.join(REPOS, repo_name))
    graph = DependencyGraph(repo.get_dependencies, max_depth,
                            filter_substring)
    return graph.build(root)


class TestRepositoryTest(unittest.TestCase):
    """Проверка чтения тестового репозитория."""

    def test_read(self):
        """Строки 'A: B C' превращаются в список смежности."""
        repo = TestRepository(os.path.join(REPOS, "simple.txt"))
        self.assertEqual(repo.get_dependencies("A"), ["B", "C"])
        self.assertEqual(repo.get_dependencies("D"), [])
        self.assertTrue(repo.has_package("F"))

    def test_bad_format(self):
        """Имя пакета не из больших латинских букв — ошибка."""
        with self.assertRaises(RepositoryError):
            TestRepository(os.path.join(REPOS, "bad_format.txt"))

    def test_missing_file(self):
        """Несуществующий файл — ошибка."""
        with self.assertRaises(RepositoryError):
            TestRepository(os.path.join(REPOS, "nope.txt"))


class DependencyGraphTest(unittest.TestCase):
    """Проверка обхода DFS, глубины, фильтра и циклов."""

    def test_transitive(self):
        """Транзитивные зависимости попадают в граф, циклов нет."""
        graph = build("simple.txt")
        self.assertEqual(set(graph.edges), set("ABCDEF"))
        self.assertEqual(graph.edges["C"], ["D", "E"])
        self.assertEqual(graph.cycles, [])

    def test_cycle(self):
        """Цикл A -> B -> C -> A находится, обход завершается."""
        graph = build("cycle.txt")
        self.assertEqual(graph.cycles, [["A", "B", "C", "A"]])

    def test_self_cycle(self):
        """Зависимость пакета от самого себя — тоже цикл."""
        graph = build("self_cycle.txt")
        self.assertIn(["A", "A"], graph.cycles)
        self.assertIn(["B", "C", "B"], graph.cycles)

    def test_max_depth(self):
        """Пакеты глубже max_depth не раскрываются."""
        graph = build("deep.txt", max_depth=3)
        self.assertEqual(list(graph.edges), ["A", "B", "C", "D"])
        self.assertEqual(graph.truncated, {"D"})

    def test_filter(self):
        """Пакеты с подстрокой фильтра не учитываются."""
        graph = build("simple.txt", filter_substring="D")
        self.assertNotIn("D", graph.edges)
        self.assertEqual(graph.edges["B"], [])

    def test_shallower_path_expands(self):
        """Пакет, найденный сначала глубоко, раскрывается при более
        коротком пути к нему."""
        deps = {"A": ["B", "D"], "B": ["C"], "C": ["D"], "D": ["E"]}
        graph = DependencyGraph(lambda name: deps.get(name, []), 2)
        graph.build("A")
        self.assertEqual(graph.edges["D"], ["E"])


if __name__ == "__main__":
    unittest.main()
