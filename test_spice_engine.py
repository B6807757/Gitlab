import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from spice_engine import (
    Circuit,
    Source,
    SpiceEngineNotFound,
    SpiceParseError,
    SpiceRunError,
    _invoke,
    build_netlist,
    engine_version,
    find_engine,
    parse_dc,
    run_dc,
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


if __name__ == "__main__":
    unittest.main()
