import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from spice_engine import (
    AcPoint,
    Circuit,
    Source,
    SpiceEngineNotFound,
    SpiceParseError,
    SpiceRunError,
    _invoke,
    build_netlist,
    engine_version,
    find_cutoffs,
    find_engine,
    parse_ac,
    parse_dc,
    parse_tran,
    run_dc,
    tran_timing,
    validate_circuit,
    validate_source,
)


DC_LOG = """
No. of Data Rows : 1
	Node                                  Voltage
	----                                  -------
	V(6)                             0.000000e+00
	V(5)                             0.000000e+00
	V(4)                             1.421184e+00
	V(3)                             8.883154e+00
	V(2)                             2.083932e+00
	V(1)                             1.200000e+01

      device                    q1
        model               q2n3904
           ic            0.00141697
           ib           4.43721e-06
          vbe              0.662517
"""

AC_LOG = """
Index   frequency       vm(5)           vm(6)
--------------------------------------------------------------------------------
0	1.000000e+01	1.000000e+00	1.741340e+00
1	1.000000e+03	1.000000e+00	1.763723e+00
2	1.000000e+07	1.000000e+00	1.741437e+00

Index   frequency       vp(5)           vp(6)
--------------------------------------------------------------------------------
0	1.000000e+01	0.000000e+00	-3.11922e+00
1	1.000000e+03	0.000000e+00	-3.13939e+00
2	1.000000e+07	0.000000e+00	-3.13000e+00
"""

TRAN_LOG = """
Index   time            v(5)            v(6)
--------------------------------------------------------------------------------
0	0.000000e+00	0.000000e+00	-8.40000e-06
1	2.500000e-04	1.000000e-02	-1.76000e-02
2	5.000000e-04	0.000000e+00	-8.00000e-06
3	7.500000e-04	-1.000000e-02	1.76000e-02
"""


class TestNetlist(unittest.TestCase):
    def test_reference_netlist_contains_topology_and_values(self):
        circuit = Circuit(12, 100e3, 22e3, 2.2e3, 1e3, 10e3, 10e-6, 10e-6)
        source = Source(0.01, 1e3)
        net = build_netlist(circuit, source, "dc")
        for line in (
            "VCC 1 0 DC 12",
            "R1 1 2 100000",
            "R2 2 0 22000",
            "RC 1 3 2200",
            "RE 4 0 1000",
            "Q1 3 2 4 Q2N3904",
            "CIN 5 2 1e-05",
            "COUT 3 6 1e-05",
            "RL 6 0 10000",
            "VIN 5 0 DC 0 AC 1 SIN(0 0.01 1000)",
        ):
            self.assertIn(line, net)
        self.assertIn(".model Q2N3904 NPN(", net)
        self.assertIn(".op", net)
        self.assertTrue(net.rstrip().endswith(".end"))

    def test_ac_uses_separate_phase_print_line(self):
        net = build_netlist(
            Circuit(12, 100e3, 22e3, 2.2e3, 1e3, 10e3, 1e-5, 1e-5),
            Source(0.01, 1e3),
            "ac",
        )
        self.assertIn(".ac dec 20 1 100meg", net)
        self.assertIn(".print ac vm(5) vm(6)", net)
        self.assertIn(".print ac vp(5) vp(6)", net)

    def test_tran_directive_follows_source_frequency(self):
        net = build_netlist(
            Circuit(12, 100e3, 22e3, 2.2e3, 1e3, 10e3, 1e-5, 1e-5),
            Source(0.01, 1e3),
            "tran",
        )
        self.assertIn(".tran 2.5e-06 0.005", net)
        self.assertIn(".print tran v(5) v(6)", net)

    def test_unknown_analysis_is_rejected(self):
        with self.assertRaises(ValueError):
            build_netlist(
                Circuit(12, 100e3, 22e3, 2.2e3, 1e3, 10e3, 1e-5, 1e-5),
                Source(0.01, 1e3),
                "fft",
            )


class TestValidation(unittest.TestCase):
    def test_zero_re_is_rejected_before_netlist(self):
        with self.assertRaisesRegex(ValueError, "RE"):
            validate_circuit(Circuit(12, 100e3, 22e3, 2.2e3, 0, 10e3, 1e-5, 1e-5))

    def test_non_finite_and_negative_values_are_rejected(self):
        for bad in (float("inf"), float("nan"), -1.0):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_circuit(Circuit(12, 100e3, 22e3, 2.2e3, bad, 10e3, 1e-5, 1e-5))

    def test_source_limits(self):
        for amp, freq in ((0, 1e3), (2.0, 1e3), (0.01, 5), (0.01, 500e3)):
            with self.subTest(amp=amp, freq=freq), self.assertRaises(ValueError):
                validate_source(Source(amp, freq))


class TestEngineDiscovery(unittest.TestCase):
    def test_explicit_missing_path_raises(self):
        with self.assertRaises(SpiceEngineNotFound):
            find_engine(str(Path(tempfile.gettempdir()) / "no-such-ngspice.exe"))

    def test_explicit_existing_path_is_returned(self):
        self.assertEqual(find_engine(sys.executable), sys.executable)

    def test_version_from_install_folder_name(self):
        self.assertEqual(engine_version(r"C:\x\ngspice-33-w7\ngspice.exe"), "ngspice-33")
        self.assertEqual(engine_version(r"C:\x\bin\ngspice.exe"), "unknown")


class TestDc(unittest.TestCase):
    def test_parse_dc_reads_node_voltages_and_collector_current(self):
        result = parse_dc(DC_LOG, "netlist", 0.05, "ngspice-33")
        self.assertAlmostEqual(result.vb, 2.083932)
        self.assertAlmostEqual(result.ve, 1.421184)
        self.assertAlmostEqual(result.vc, 8.883154)
        self.assertAlmostEqual(result.vce, 8.883154 - 1.421184)
        self.assertAlmostEqual(result.ic, 0.00141697)

    def test_missing_node_is_a_parse_error(self):
        with self.assertRaises(SpiceParseError):
            parse_dc(DC_LOG.replace("V(3)", "V(9)"), "netlist", 0.0, "ngspice-33")

    def test_nonzero_exit_is_a_run_error(self):
        bad = subprocess.CompletedProcess([], 1, "", "boom")
        with mock.patch("spice_engine.subprocess.run", return_value=bad):
            with self.assertRaisesRegex(SpiceRunError, "boom"):
                _invoke("* netlist", sys.executable, 20)

    def test_timeout_is_a_run_error(self):
        with mock.patch(
            "spice_engine.subprocess.run",
            side_effect=subprocess.TimeoutExpired("ngspice", 20),
        ):
            with self.assertRaisesRegex(SpiceRunError, "20"):
                _invoke("* netlist", sys.executable, 20)

    def test_run_dc_writes_netlist_and_parses_log(self):
        with mock.patch("spice_engine._invoke", return_value=DC_LOG) as invoke:
            result = run_dc(
                Circuit(12, 100e3, 22e3, 2.2e3, 1e3, 10e3, 1e-5, 1e-5),
                Source(0.01, 1e3),
                exe=sys.executable,
            )
        self.assertAlmostEqual(result.ic, 0.00141697)
        self.assertIn(".op", invoke.call_args.args[0])


class TestAc(unittest.TestCase):
    def test_parse_ac_converts_phase_to_degrees(self):
        result = parse_ac(AC_LOG, "n", 0.0, "ngspice-33")
        self.assertEqual(len(result.points), 3)
        self.assertAlmostEqual(result.points[1].gain, 1.763723)
        self.assertAlmostEqual(result.points[1].gain_db, 20 * math.log10(1.763723))
        self.assertAlmostEqual(result.points[1].phase_deg, -179.87, places=1)
        self.assertAlmostEqual(result.gain_1khz.gain, 1.763723)

    def test_missing_phase_table_is_a_parse_error(self):
        with self.assertRaises(SpiceParseError):
            parse_ac(AC_LOG.split("Index   frequency       vp")[0], "n", 0.0, "v")

    def test_paginated_table_keeps_rows_after_form_feed(self):
        paginated = AC_LOG.replace(
            "1\t1.000000e+03",
            "\nIndex   frequency       vm(5)           vm(6)\n"
            "--------------------------------------------------------------------------------\n"
            "1\t1.000000e+03",
            1,
        )
        result = parse_ac(paginated, "n", 0.0, "ngspice-33")
        self.assertEqual(len(result.points), 3)

    def test_cutoffs_interpolate_and_flat_response_is_undetermined(self):
        points = [
            AcPoint(f, g, 0, 0)
            for f, g in ((10, 1.0), (100, 10.0), (1000, 10.0), (10000, 1.0))
        ]
        low, high = find_cutoffs(points)
        self.assertAlmostEqual(low, 47.29, places=1)
        self.assertAlmostEqual(high, 2115.0, delta=5.0)

        flat = [AcPoint(f, 2.0, 0, 0) for f in (10, 100, 1000)]
        self.assertEqual(find_cutoffs(flat), (None, None))


class TestTran(unittest.TestCase):
    def test_timing_uses_five_ms_or_three_cycles(self):
        self.assertEqual(tran_timing(1e3), (2.5e-06, 0.005))
        self.assertAlmostEqual(tran_timing(100)[1], 0.03)
        self.assertEqual(tran_timing(1)[1], 0.2)

    def test_parse_tran_reports_pp_and_inversion(self):
        result = parse_tran(TRAN_LOG, "n", 0.0, "ngspice-33")
        self.assertEqual(len(result.points), 4)
        self.assertAlmostEqual(result.vin_pp, 0.02)
        self.assertAlmostEqual(result.vout_pp, 0.0352)
        self.assertTrue(result.inverted)

    def test_short_table_is_a_parse_error(self):
        broken = TRAN_LOG.splitlines()[0] + "\n" + TRAN_LOG.splitlines()[2]
        with self.assertRaises(SpiceParseError):
            parse_tran(broken, "n", 0.0, "v")


if __name__ == "__main__":
    unittest.main()
