"""Построение графа зависимостей рекурсивным обходом в глубину (DFS)."""

ROOT_DEPTH = 0


class DependencyGraph:
    """Граф зависимостей пакета с учётом транзитивности.

    Атрибуты после build():
    edges     — список смежности {пакет: [его зависимости]};
    cycles    — найденные циклы, например ["A", "B", "A"];
    truncated — пакеты, не раскрытые из-за ограничения глубины.
    """

    def __init__(self, get_deps, max_depth, filter_substring=""):
        """Сохраняет функцию получения зависимостей и ограничения."""
        self.get_deps = get_deps
        self.max_depth = max_depth
        self.filter_substring = filter_substring
        self.edges = {}
        self.cycles = []
        self.truncated = set()
        self._best_depth = {}
        self._path = []

    def build(self, root):
        """Строит граф от корневого пакета и возвращает self."""
        self._visit(root, ROOT_DEPTH)
        return self

    def is_filtered(self, name):
        """Проверяет, что пакет исключается фильтром по подстроке."""
        return bool(self.filter_substring) and self.filter_substring in name

    def _already_visited(self, pkg, depth):
        """Проверяет, что пакет уже обработан не глубже, чем сейчас."""
        best = self._best_depth.get(pkg)
        return best is not None and best <= depth

    def _visit(self, pkg, depth):
        """Рекурсивно обходит зависимости пакета (DFS)."""
        if self._already_visited(pkg, depth):
            return
        self._best_depth[pkg] = depth
        self.edges.setdefault(pkg, [])
        if depth >= self.max_depth:
            self.truncated.add(pkg)
            return
        self.truncated.discard(pkg)
        children = [d for d in self.get_deps(pkg) if not self.is_filtered(d)]
        self.edges[pkg] = children
        self._path.append(pkg)
        for dep in children:
            if dep in self._path:
                self._add_cycle(dep)
            else:
                self._visit(dep, depth + 1)
        self._path.pop()

    def _add_cycle(self, dep):
        """Запоминает цикл: часть текущего пути от dep и снова dep."""
        cycle = self._path[self._path.index(dep):] + [dep]
        known = [set(c) for c in self.cycles]
        if set(cycle) not in known:
            self.cycles.append(cycle)

    def format_lines(self):
        """Возвращает текстовое представление графа построчно."""
        lines = [f"Граф зависимостей, пакетов: {len(self.edges)}"]
        for pkg, deps in self.edges.items():
            if pkg in self.truncated:
                text = "(не раскрыт: достигнута максимальная глубина)"
            else:
                text = ", ".join(deps) if deps else "(нет зависимостей)"
            lines.append(f"  {pkg} -> {text}")
        if not self.cycles:
            lines.append("Циклических зависимостей нет.")
        for cycle in self.cycles:
            lines.append("Цикл: " + " -> ".join(cycle))
        return lines
