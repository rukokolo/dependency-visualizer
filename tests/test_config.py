"""Тесты чтения и проверки конфигурации (этап 1)."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from config import PARAMS, ConfigError, load_config  # noqa: E402

CONFIGS = os.path.join(ROOT, "tests", "configs")

BAD_CONFIGS = {
    "bad_missing.csv": "не заданы параметры: max_depth",
    "bad_unknown.csv": "неизвестный параметр 'color'",
    "bad_name.csv": "недопустимое имя пакета",
    "bad_url.csv": "ожидается URL",
    "bad_test_path.csv": "файл тестового репозитория не найден",
    "bad_version.csv": "версия не может быть пустой",
    "bad_bool.csv": "ожидается true или false",
    "bad_depth.csv": "глубина должна быть >= 1",
}


class LoadConfigTest(unittest.TestCase):
    """Проверка функции load_config."""

    def test_valid_config(self):
        """Корректный конфиг читается, значения приводятся к типам."""
        cfg = load_config(os.path.join(ROOT, "config.csv"))
        self.assertEqual(set(cfg), set(PARAMS))
        self.assertEqual(cfg["package_name"], "curl")
        self.assertIs(cfg["test_mode"], False)
        self.assertEqual(cfg["max_depth"], 3)

    def test_missing_file(self):
        """Несуществующий файл конфигурации даёт ConfigError."""
        with self.assertRaises(ConfigError):
            load_config(os.path.join(CONFIGS, "nonexistent.csv"))

    def test_bad_configs(self):
        """Каждая ошибочная конфигурация даёт понятное сообщение."""
        for name, message in BAD_CONFIGS.items():
            with self.subTest(config=name):
                with self.assertRaises(ConfigError) as context:
                    load_config(os.path.join(CONFIGS, name))
                self.assertIn(message, str(context.exception))


if __name__ == "__main__":
    unittest.main()
