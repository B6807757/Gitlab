import unittest

from plots import bode_svg, transient_svg
from spice_engine import AcPoint, TranPoint


class TestBode(unittest.TestCase):
    def test_bode_has_two_panels_axes_units_and_all_points(self):
        points = (
            AcPoint(10, 1.7, 4.6, -179.0),
            AcPoint(1e3, 1.76, 4.9, -179.9),
            AcPoint(1e6, 1.7, 4.6, -179.0),
        )
        svg = bode_svg(points)
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn('viewBox="0 0 760 440"', svg)
        for text in ("ความถี่ (Hz)", "ขนาด (dB)", "เฟส (องศา)", "ngspice"):
            self.assertIn(text, svg)
        self.assertEqual(svg.count("<polyline"), 2)
        self.assertEqual(svg.count("data-point"), 6)

    def test_empty_bode_is_rejected(self):
        with self.assertRaises(ValueError):
            bode_svg(())


class TestTransient(unittest.TestCase):
    def test_transient_has_two_traces_legend_and_units(self):
        points = (
            TranPoint(0, 0, 0),
            TranPoint(0.0005, 0.01, -0.017),
            TranPoint(0.001, 0, 0),
        )
        svg = transient_svg(points)
        self.assertIn("เวลา (ms)", svg)
        self.assertIn("แรงดัน (V)", svg)
        self.assertIn("Vin", svg)
        self.assertIn("Vout", svg)
        self.assertEqual(svg.count("<polyline"), 2)
        self.assertEqual(svg.count("data-point"), 6)

    def test_single_point_still_renders(self):
        self.assertIn("<svg", transient_svg((TranPoint(0, 0, 0),)))


if __name__ == "__main__":
    unittest.main()
