import unittest

from app.core.config import Settings


class RuntimeSecurityTests(unittest.TestCase):
    def test_secret_key_is_required_and_must_be_long(self):
        for value in (None, "short", "your-secret-key-here"):
            with self.subTest(value=value):
                with self.assertRaises(RuntimeError):
                    Settings(SECRET_KEY=value, _env_file=None).require_secret_key()

    def test_explicit_strong_secret_is_accepted(self):
        value = "a-project-specific-secret-with-32-characters"
        self.assertEqual(
            value,
            Settings(SECRET_KEY=value, _env_file=None).require_secret_key(),
        )


if __name__ == "__main__":
    unittest.main()
