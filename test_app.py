import unittest

from app import app, parse_number, parse_resistance


class TestParsing(unittest.TestCase):
    def test_plain_numbers(self):
        self.assertAlmostEqual(parse_number("12"), 12.0)
        self.assertAlmostEqual(parse_number(" 0.7 "), 0.7)

    def test_resistance_suffixes(self):
        cases = (
            ("47k", 47000.0),
            ("4.7k", 4700.0),
            ("1M", 1e6),
            ("47kΩ", 47000.0),
            ("47kohm", 47000.0),
            ("1000", 1000.0),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_resistance(text), expected)

    def test_rejects_expressions_and_separators(self):
        for text in ("4.7*1000", "47,000", "", "abc", "47kk"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_resistance(text)


class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_renders_form(self):
        resp = self.client.get("/")
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("VCC", body)
        self.assertIn('name="r1"', body)
        self.assertIn('value="47k"', body)


if __name__ == "__main__":
    unittest.main()
