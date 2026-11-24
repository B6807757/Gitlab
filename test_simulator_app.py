import unittest
from unittest import mock

from app import SIM_DEFAULTS, app, parse_capacitance
from spice_engine import DcResult, SpiceEngineNotFound


class TestCapacitance(unittest.TestCase):
    def test_suffixes(self):
        for text, expected in (
            ("10u", 10e-6),
            ("10µF", 10e-6),
            ("0.1u", 1e-7),
            ("4.7n", 4.7e-9),
            ("100p", 100e-12),
            ("1m", 1e-3),
        ):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_capacitance(text), expected)

    def test_bad_text_is_rejected(self):
        for text in ("", "abc", "10x", "-1u", "1u2"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_capacitance(text)


class TestSimulatorRoute(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_renders_form_and_defaults(self):
        html = self.client.get("/simulator").get_data(as_text=True)
        self.assertIn("CE Amplifier Simulator", html)
        self.assertIn('value="100k"', html)
        self.assertIn("ngspice", html)
        self.assertIn("Analytical", html)

    def test_post_dc_shows_spice_and_analytical_separately(self):
        dc = DcResult(
            2.083932,
            1.421184,
            8.883154,
            7.46197,
            0.00141697,
            "log",
            "netlist",
            0.05,
            "ngspice-33",
        )
        with mock.patch("app.run_simulation", return_value=dc):
            html = self.client.post(
                "/simulator", data={"analysis": "dc", **SIM_DEFAULTS}
            ).get_data(as_text=True)
        self.assertIn("ngspice (SPICE)", html)
        self.assertIn("สมการประมาณ (Analytical)", html)
        self.assertIn("1.417", html)
        self.assertIn("Q2N3904", html)
        self.assertIn("Success", html)
        self.assertNotIn("ไม่สามารถจำลอง", html)

    def test_engine_failure_shows_error_without_chart_or_success(self):
        with mock.patch(
            "app.run_simulation", side_effect=SpiceEngineNotFound("ไม่พบ ngspice")
        ):
            response = self.client.post(
                "/simulator", data={"analysis": "dc", **SIM_DEFAULTS}
            )
        html = response.get_data(as_text=True)
        self.assertIn("ไม่พบ ngspice", html)
        self.assertNotIn("<svg", html)
        self.assertNotIn("Success", html)

    def test_zero_re_is_rejected_before_simulation(self):
        with mock.patch("app.run_simulation") as runner:
            response = self.client.post(
                "/simulator", data={"analysis": "dc", **SIM_DEFAULTS, "re": "0"}
            )
        self.assertIn("RE", response.get_data(as_text=True))
        runner.assert_not_called()

    def test_lab3_home_is_unchanged(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("BJT Common-Emitter DC Bias", html)


if __name__ == "__main__":
    unittest.main()
