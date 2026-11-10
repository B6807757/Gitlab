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


FORM = {
    "vcc": "12",
    "r1": "47k",
    "r2": "10k",
    "rc": "2.2k",
    "re": "1k",
    "beta": "150",
    "vbe": "0.7",
}


class TestResults(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_reference_qpoint(self):
        resp = self.client.post("/", data=FORM)
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("1.32 mA", body)
        self.assertIn("7.76 V", body)
        self.assertIn("Active", body)
        self.assertIn("1.41 mA", body)
        self.assertIn("6.16", body)

    def test_invalid_input_is_readable_and_keeps_typed_value(self):
        resp = self.client.post("/", data={**FORM, "r1": "0"})
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ต้องมากกว่า 0", body)
        self.assertIn('value="0"', body)
        self.assertNotIn("Traceback", body)

    def test_non_numeric_input(self):
        resp = self.client.post("/", data={**FORM, "vcc": "abc"})
        body = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("กรุณากรอกเป็นตัวเลข", body)

    def test_saturation_warning(self):
        resp = self.client.post("/", data={**FORM, "rc": "47k"})
        body = resp.get_data(as_text=True)
        self.assertIn("Saturation", body)
        self.assertIn("246 µA", body)

    def test_cutoff_warning_and_dash_in_comparison(self):
        resp = self.client.post("/", data={**FORM, "r2": "1k"})
        body = resp.get_data(as_text=True)
        self.assertIn("Cutoff", body)
        self.assertIn("—", body)

    def test_active_result_confirms_agreement(self):
        body = self.client.post("/", data=FORM).get_data(as_text=True)
        self.assertIn("✓", body)

    def test_saturation_result_dashes_the_agreement_row(self):
        body = self.client.post("/", data={**FORM, "rc": "47k"}).get_data(as_text=True)
        self.assertIn("—", body)
        self.assertNotIn("✓", body)


class TestDiagram(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_shows_schematic_with_default_values(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn("<svg", body)
        self.assertIn('role="img"', body)
        for label in ("12.0 V", "47.0 kΩ", "10.0 kΩ", "2.20 kΩ", "1.00 kΩ"):
            with self.subTest(label=label):
                self.assertIn(label, body)

    def test_diagram_follows_submitted_values(self):
        body = self.client.post("/", data={**FORM, "r1": "100k"}).get_data(as_text=True)
        self.assertIn("100 kΩ", body)
        self.assertIn("366 µA", body)
        self.assertNotIn("47.0 kΩ", body)

    def test_invalid_input_keeps_a_default_schematic(self):
        body = self.client.post("/", data={**FORM, "r1": "0"}).get_data(as_text=True)
        self.assertIn("<svg", body)
        self.assertIn("ค่าตั้งต้น", body)

    def test_active_result_shows_a_region_verdict(self):
        body = self.client.post("/", data=FORM).get_data(as_text=True)
        self.assertIn("โซนแอกทีฟปกติ", body)
        self.assertIn("7.76 V", body)


if __name__ == "__main__":
    unittest.main()
