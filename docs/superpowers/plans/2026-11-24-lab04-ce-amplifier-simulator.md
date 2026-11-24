# Lab 04 CE Amplifier Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing Lab 3 Flask BJT bias app with real ngspice `.op` / `.ac` / `.tran` simulation for one reference CE voltage-divider circuit, rendered as server-side SVG with honest error paths.

**Architecture:** Keep `app.py` + `bjt.py` and the three Lab 3 bias modes untouched in behaviour. Add `spice_engine.py` (validate → netlist → subprocess → parse), `plots.py` (SVG from parsed data), and a separate `/simulator` route + `templates/simulator.html`. Every number shown comes from the parsed ngspice log of that run; analytical values come only from `bjt.analyze()` and are labelled separately.

**Tech Stack:** Python 3.12, Flask 3, ngspice-33 batch mode, Jinja2, inline SVG, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-24-lab04-ce-amplifier-simulator-design.md`

## Global Constraints

- Preserve all three Lab 3 DC bias modes, their results, and every existing test (`python -m unittest -v`).
- Only the reference CE voltage-divider circuit is simulated: VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, RL 10 kΩ, Cin 10 µF, Cout 10 µF, source 10 mV peak / 1 kHz.
- BJT card is exactly the approved Philips 2N3904 card; never invent device values.
- `subprocess.run` gets an argument list, `shell=False`, a 20 s timeout, and a fresh `TemporaryDirectory` per run.
- No mock traces, no hard-coded result numbers, no stale results shown as Success.
- SPICE and analytical results are always visually separated and labelled.
- ngspice-33 quirks: `vp()` needs its own `.print ac vp(...)` line and returns radians.
- Thai UI copy consistent with Lab 3; units always shown.

## Review Focus

- ngspice missing or moved → clear error, no graph, no Success badge.
- ngspice hangs or exits non-zero → timeout/error surfaced within 20 s, no partial success.
- Log table format changes (missing phase table, short rows, `NaN`) → `SpiceParseError`, never an empty "successful" result.
- Source frequency at range edges (10 Hz / 100 kHz) → transient window still stated and plotted honestly.
- Degenerate form input (0, negative, huge, `1e999`, unit typos) → rejected before netlist creation, no injection into the solver.

---

### Task 1: Engine discovery, validation, and netlist generation

**Files:**
- Create: `spice_engine.py`
- Test: `test_spice_engine.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `MODEL_NAME: str = "Q2N3904"`, `MODEL_CARD: str` (multi-line `.model ...` card)
  - `@dataclass(frozen=True) Circuit(vcc, r1, r2, rc, re, rl, cin, cout: float)`
  - `@dataclass(frozen=True) Source(amplitude_v, frequency_hz: float)`
  - `class SpiceError(Exception)`, `SpiceEngineNotFound(SpiceError)`, `SpiceRunError(SpiceError)`, `SpiceParseError(SpiceError)`
  - `find_engine(explicit: str | None = None) -> str`
  - `engine_version(exe: str) -> str`
  - `validate_circuit(circuit: Circuit) -> None` (raises `ValueError`)
  - `validate_source(source: Source) -> None` (raises `ValueError`)
  - `build_netlist(circuit: Circuit, source: Source, analysis: str) -> str` (`analysis` in `"dc"`, `"ac"`, `"tran"`; raises `ValueError` otherwise)

- [ ] **Step 1: Write the failing tests**

```python
class TestNetlist(unittest.TestCase):
    def test_reference_netlist_contains_topology_and_values(self):
        circuit = Circuit(12, 100e3, 22e3, 2.2e3, 1e3, 10e3, 10e-6, 10e-6)
        source = Source(0.01, 1e3)
        net = build_netlist(circuit, source, "dc")
        for line in ("VCC 1 0 DC 12", "R1 1 2 100000", "R2 2 0 22000",
                     "RC 1 3 2200", "RE 4 0 1000", "Q1 3 2 4 Q2N3904",
                     "CIN 5 2 1e-05", "COUT 3 6 1e-05", "RL 6 0 10000",
                     "VIN 5 0 DC 0 AC 1 SIN(0 0.01 1000)"):
            self.assertIn(line, net)
        self.assertIn(".model Q2N3904 NPN(", net)
        self.assertIn(".op", net)
        self.assertTrue(net.rstrip().endswith(".end"))

    def test_ac_uses_separate_phase_print_line(self):
        net = build_netlist(Circuit(12, 100e3, 22e3, 2.2e3, 1e3, 10e3, 1e-5, 1e-5), Source(0.01, 1e3), "ac")
        self.assertIn(".ac dec 20 1 100meg", net)
        self.assertIn(".print ac vm(5) vm(6)", net)
        self.assertIn(".print ac vp(5) vp(6)", net)

    def test_tran_directive_follows_source_frequency(self):
        net = build_netlist(Circuit(12, 100e3, 22e3, 2.2e3, 1e3, 10e3, 1e-5, 1e-5), Source(0.01, 1e3), "tran")
        self.assertIn(".tran 2.5e-06 0.005", net)
        self.assertIn(".print tran v(5) v(6)", net)

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest test_spice_engine -v`
Expected: `ModuleNotFoundError: No module named 'spice_engine'`

- [ ] **Step 3: Implement `spice_engine.py`**

Use `format(value, ".10g")` for every numeric value. Ranges: resistances and capacitors `> 0` and `<= 1e9`; VCC `0 < vcc <= 100`; amplitude `0 < amp <= 1.0` V; frequency `10 <= f <= 100e3` Hz. `find_engine` order: explicit → `NGSPICE_EXE` → `shutil.which("ngspice")` → known `%LOCALAPPDATA%\Programs\ngspice\ngspice-33-w7\ngspice.exe`. `engine_version` regex `ngspice[-_]?(\d+(?:\.\d+)*)` on the path, else `"unknown"`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest test_spice_engine -v`
Expected: all Task 1 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add spice_engine.py test_spice_engine.py
git commit -m "feat: generate validated ngspice netlists"
```

---

### Task 2: Batch runner and DC operating-point parser

**Files:**
- Modify: `spice_engine.py`
- Test: `test_spice_engine.py`

**Interfaces:**
- Consumes: Task 1 types and `build_netlist`.
- Produces:
  - `@dataclass(frozen=True) DcResult(vb, ve, vc, vce, ic: float; log: str; netlist: str; duration_s: float; engine_version: str)`
  - `run_dc(circuit: Circuit, source: Source, *, exe: str | None = None, timeout: float = 20.0) -> DcResult`
  - `_invoke(netlist: str, exe: str, timeout: float) -> str` (returns log text; raises `SpiceRunError`)
  - `parse_dc(log: str, netlist: str, duration_s: float, engine_version: str) -> DcResult`

- [ ] **Step 1: Write the failing tests**

Use this fixture (exact ngspice-33 text) inside the test module:

```python
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

class TestDc(unittest.TestCase):
    def test_parse_dc_reads_node_voltages_and_collector_current(self):
        r = parse_dc(DC_LOG, "netlist", 0.05, "ngspice-33")
        self.assertAlmostEqual(r.vb, 2.083932)
        self.assertAlmostEqual(r.ve, 1.421184)
        self.assertAlmostEqual(r.vc, 8.883154)
        self.assertAlmostEqual(r.vce, 8.883154 - 1.421184)
        self.assertAlmostEqual(r.ic, 0.00141697)

    def test_missing_node_is_a_parse_error(self):
        with self.assertRaises(SpiceParseError):
            parse_dc(DC_LOG.replace("V(3)", "V(9)"), "netlist", 0.0, "ngspice-33")

    def test_nonzero_exit_is_a_run_error(self):
        bad = subprocess.CompletedProcess([], 1, "", "boom")
        with mock.patch("spice_engine.subprocess.run", return_value=bad):
            with self.assertRaisesRegex(SpiceRunError, "boom"):
                _invoke("* netlist", sys.executable, 20)

    def test_timeout_is_a_run_error(self):
        with mock.patch("spice_engine.subprocess.run",
                        side_effect=subprocess.TimeoutExpired("ngspice", 20)):
            with self.assertRaisesRegex(SpiceRunError, "20"):
                _invoke("* netlist", sys.executable, 20)

    def test_run_dc_writes_netlist_and_parses_log(self):
        with mock.patch("spice_engine._invoke", return_value=DC_LOG) as invoke:
            result = run_dc(Circuit(12, 100e3, 22e3, 2.2e3, 1e3, 10e3, 1e-5, 1e-5),
                            Source(0.01, 1e3), exe=sys.executable)
        self.assertAlmostEqual(result.ic, 0.00141697)
        self.assertIn(".op", invoke.call_args.args[0])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest test_spice_engine -v`
Expected: FAIL with `NameError` / `ImportError` for `parse_dc`, `run_dc`.

- [ ] **Step 3: Implement runner and parser**

`_invoke` writes `circuit.cir` into `tempfile.TemporaryDirectory()`, runs
`[exe, "-b", "-o", "run.log", "circuit.cir"]` with `cwd=tmp`, `capture_output=True`,
`text=True`, `timeout=timeout`; raises `SpiceRunError` on `TimeoutExpired`, non-zero
return code (include stderr/stdout tail), or empty log. Read `run.log` with
`encoding="utf-8", errors="replace"`.

`parse_dc`: collect `V(n)` with regex `^V\((\d+)\)\s+(-?[\d.]+e[+-]\d+)`; require nodes
1–4; find the `device q1` block and its `ic` line; raise `SpiceParseError` if anything
is missing or non-finite.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest test_spice_engine -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add spice_engine.py test_spice_engine.py
git commit -m "feat: run ngspice DC operating point and parse results"
```

---

### Task 3: AC and transient parsing, timing, and metrics

**Files:**
- Modify: `spice_engine.py`
- Test: `test_spice_engine.py`

**Interfaces:**
- Consumes: Task 1/2 types.
- Produces:
  - `@dataclass(frozen=True) AcPoint(frequency_hz, gain, gain_db, phase_deg: float)`
  - `@dataclass(frozen=True) AcResult(points: tuple[AcPoint, ...], gain_1khz: AcPoint | None, f_low_hz: float | None, f_high_hz: float | None, log, netlist: str, duration_s: float, engine_version: str)`
  - `@dataclass(frozen=True) TranPoint(time_s, vin, vout: float)`
  - `@dataclass(frozen=True) TranResult(points: tuple[TranPoint, ...], vin_pp, vout_pp: float, inverted: bool, stop_s, step_s: float, log, netlist: str, duration_s: float, engine_version: str)`
  - `tran_timing(frequency_hz: float) -> tuple[float, float]` → `(step_s, stop_s)`
  - `run_ac(...) -> AcResult`, `run_tran(...) -> TranResult`, `parse_ac(log, netlist, duration_s, engine_version) -> AcResult`, `parse_tran(...) -> TranResult`
  - `find_cutoffs(points: Sequence[AcPoint]) -> tuple[float | None, float | None]`

- [ ] **Step 1: Write the failing tests**

```python
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

class TestAc(unittest.TestCase):
    def test_parse_ac_converts_phase_to_degrees(self):
        r = parse_ac(AC_LOG, "n", 0.0, "ngspice-33")
        self.assertEqual(len(r.points), 3)
        self.assertAlmostEqual(r.points[1].gain, 1.763723)
        self.assertAlmostEqual(r.points[1].gain_db, 20 * math.log10(1.763723))
        self.assertAlmostEqual(r.points[1].phase_deg, -179.87, places=1)
        self.assertAlmostEqual(r.gain_1khz.gain, 1.763723)

    def test_missing_phase_table_is_a_parse_error(self):
        with self.assertRaises(SpiceParseError):
            parse_ac(AC_LOG.split("Index   frequency       vp")[0], "n", 0.0, "v")

    def test_cutoffs_interpolate_and_flat_response_is_undetermined(self):
        pts = [AcPoint(f, g, 0, 0) for f, g in
               ((10, 1.0), (100, 10.0), (1000, 10.0), (10000, 1.0))]
        self.assertAlmostEqual(find_cutoffs(pts)[0], 31.622, places=2)
        self.assertAlmostEqual(find_cutoffs(pts)[1], 3162.27, places=0)
        flat = [AcPoint(f, 2.0, 0, 0) for f in (10, 100, 1000)]
        self.assertEqual(find_cutoffs(flat), (None, None))

class TestTran(unittest.TestCase):
    def test_timing_uses_five_ms_or_three_cycles(self):
        self.assertEqual(tran_timing(1e3), (2.5e-06, 0.005))
        self.assertAlmostEqual(tran_timing(100)[1], 0.03)
        self.assertEqual(tran_timing(1)[1], 0.2)

    def test_parse_tran_reports_pp_and_inversion(self):
        r = parse_tran(TRAN_LOG, "n", 0.0, "ngspice-33")
        self.assertEqual(len(r.points), 4)
        self.assertAlmostEqual(r.vin_pp, 0.02)
        self.assertAlmostEqual(r.vout_pp, 0.0352)
        self.assertTrue(r.inverted)

    def test_short_table_is_a_parse_error(self):
        with self.assertRaises(SpiceParseError):
            parse_tran(TRAN_LOG.splitlines()[0] + "\n" + TRAN_LOG.splitlines()[2], "n", 0.0, "v")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest test_spice_engine -v`
Expected: FAIL for missing `parse_ac` / `tran_timing`.

- [ ] **Step 3: Implement AC/tran parsing and metrics**

Parse tables by header line (`Index` + `frequency`/`time`), map column names to arrays, pair magnitude and phase tables by row index. Convert `vp` radians → degrees and wrap to `(-180, 180]`. `gain_db = 20*log10(gain)` (reject gain ≤ 0). `find_cutoffs` uses `max_gain / sqrt(2)` and log-frequency interpolation; return `None` when no crossing. Transient window/step per `tran_timing`; `vin_pp`/`vout_pp` over the last 50 % of samples; `inverted = covariance(vin, vout) < 0` over the same span.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest test_spice_engine -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add spice_engine.py test_spice_engine.py
git commit -m "feat: parse ngspice AC and transient results"
```

---

### Task 4: Server-side SVG plots

**Files:**
- Create: `plots.py`
- Test: `test_plots.py`

**Interfaces:**
- Consumes: `AcPoint`, `TranPoint` from Task 3.
- Produces:
  - `bode_svg(points: Sequence[AcPoint], *, width: int = 760, height: int = 440) -> str`
  - `transient_svg(points: Sequence[TranPoint], *, width: int = 760, height: int = 320) -> str`

- [ ] **Step 1: Write the failing tests**

```python
class TestBode(unittest.TestCase):
    def test_bode_has_two_panels_axes_units_and_all_points(self):
        pts = (AcPoint(10, 1.7, 4.6, -179.0), AcPoint(1e3, 1.76, 4.9, -179.9),
               AcPoint(1e6, 1.7, 4.6, -179.0))
        svg = bode_svg(pts)
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
        pts = (TranPoint(0, 0, 0), TranPoint(0.0005, 0.01, -0.017),
               TranPoint(0.001, 0, 0))
        svg = transient_svg(pts)
        self.assertIn("เวลา (ms)", svg)
        self.assertIn("แรงดัน (V)", svg)
        self.assertIn("Vin", svg)
        self.assertIn("Vout", svg)
        self.assertEqual(svg.count("<polyline"), 2)
        self.assertEqual(svg.count("data-point"), 6)

    def test_single_point_still_renders(self):
        self.assertIn("<svg", transient_svg((TranPoint(0, 0, 0),)))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest test_plots -v`
Expected: `ModuleNotFoundError: No module named 'plots'`.

- [ ] **Step 3: Implement `plots.py`**

Pure functions returning SVG strings. Helpers: `_scale`, `_ticks`, `_polyline`, `_axis`.
Log-x for Bode (`log10` of frequency), decade ticks, magnitude panel 0–55 % height,
phase panel 55–100 %. Transient uses milliseconds. Pad a zero-span y-range by ±10 %
(or ±1 unit). Escape nothing beyond fixed Thai/ASCII labels; all coordinates are numbers.
Include `<title>` and `aria-label` for accessibility, plus a caption line
`ngspice · Q2N3904` inside the SVG so provenance travels with the image.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest test_plots -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plots.py test_plots.py
git commit -m "feat: render ngspice results as SVG charts"
```

---

### Task 5: `/simulator` route, template, and styles

**Files:**
- Modify: `app.py` (imports near top; new helpers after `parse_resistance`; new routes after `index`)
- Create: `templates/simulator.html`
- Modify: `static/style.css` (append)
- Modify: `templates/index.html` (one link in the header only)
- Test: `test_simulator_app.py`

**Interfaces:**
- Consumes: `spice_engine` (`Circuit`, `Source`, `DcResult`, `AcResult`, `TranResult`, `SpiceError`, `run_dc`, `run_ac`, `run_tran`, `find_engine`, `engine_version`, `MODEL_NAME`), `plots.bode_svg`, `plots.transient_svg`, `bjt.BiasInputs`, `bjt.analyze`.
- Produces:
  - `parse_capacitance(text: str) -> float`
  - `SIM_DEFAULTS: dict[str, str]` with `vcc="12" r1="100k" r2="22k" rc="2.2k" re="1k" rl="10k" cin="10u" cout="10u" amp_mv="10" freq="1k" beta="150" vbe="0.70"`
  - `run_simulation(circuit: Circuit, source: Source, analysis: str) -> DcResult | AcResult | TranResult` (module-level, dispatches to `run_dc` / `run_ac` / `run_tran`; tests patch `app.run_simulation`)
  - routes `GET /simulator`, `POST /simulator`

- [ ] **Step 1: Write the failing tests**

```python
class TestCapacitance(unittest.TestCase):
    def test_suffixes(self):
        for text, expected in (("10u", 10e-6), ("10µF", 10e-6), ("0.1u", 1e-7),
                               ("4.7n", 4.7e-9), ("100p", 100e-12), ("1m", 1e-3)):
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_capacitance(text), expected)

class TestSimulatorRoute(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_renders_form_and_defaults(self):
        html = self.client.get("/simulator").get_data(as_text=True)
        self.assertIn("CE Amplifier Simulator", html)
        self.assertIn('value="100k"', html)
        self.assertIn("ngspice", html)

    def test_post_dc_shows_spice_and_analytical_separately(self):
        dc = DcResult(2.083932, 1.421184, 8.883154, 7.46197, 0.00141697,
                      "log", "netlist", 0.05, "ngspice-33")
        with mock.patch("app.run_simulation", return_value=dc):
            html = self.client.post("/simulator", data={"analysis": "dc", **SIM_DEFAULTS}).get_data(as_text=True)
        self.assertIn("ngspice (SPICE)", html)
        self.assertIn("สมการประมาณ (Analytical)", html)
        self.assertIn("1.417", html)
        self.assertIn("Q2N3904", html)
        self.assertNotIn("ไม่สามารถจำลอง", html)

    def test_engine_failure_shows_error_without_chart_or_success(self):
        with mock.patch("app.run_simulation", side_effect=SpiceEngineNotFound("ไม่พบ ngspice")):
            resp = self.client.post("/simulator", data={"analysis": "dc", **SIM_DEFAULTS})
        html = resp.get_data(as_text=True)
        self.assertIn("ไม่พบ ngspice", html)
        self.assertNotIn("<svg", html)
        self.assertNotIn("สำเร็จ", html)

    def test_zero_re_is_rejected_before_simulation(self):
        with mock.patch("app.run_simulation") as runner:
            resp = self.client.post("/simulator", data={"analysis": "dc", **SIM_DEFAULTS, "re": "0"})
        self.assertIn("RE", resp.get_data(as_text=True))
        runner.assert_not_called()

    def test_lab3_home_is_unchanged(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("BJT Common-Emitter DC Bias", html)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest test_simulator_app -v`
Expected: 404 for `/simulator`, `NameError` for `parse_capacitance`.

- [ ] **Step 3: Implement route and template**

`POST` flow: read `analysis`; build `Circuit`/`Source` from parsed values; call
`validate_circuit`/`validate_source`; on `ValueError` re-render with the error and the
submitted raw values, no results. Then call `run_simulation`; catch `SpiceError` →
render error with engine/model status and (if present) the log tail, no charts.
For DC, also compute `analyze(BiasInputs(...))` and a per-quantity delta; for AC call
`bode_svg`; for tran call `transient_svg`. Pass `engine=find_engine()` and
`version=engine_version(...)` for the status box (never fatal for the page).
Always render `netlist` and `log` inside `<details>`.

`simulator.html` sections: header + link back to `/`, circuit form (grouped inputs with
units), source form, β/VBE group labelled “ใช้กับการคำนวณ Analytical เท่านั้น”,
three submit buttons, status box (engine/model/analysis/duration/result badge),
results per analysis, `<details>` netlist + log, and a note that SPICE uses the model’s
BF=300. All charts are `{{ svg|safe }}`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest test_simulator_app -v` then `python -m unittest -v`
Expected: new tests PASS and the original 34+ tests still PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py templates/simulator.html templates/index.html static/style.css test_simulator_app.py
git commit -m "feat: add CE amplifier simulator page"
```

---

### Task 6: Real ngspice validation, documentation, and publish

**Files:**
- Modify: `README.md`, `docs/validation.md`
- Create: `docs/evidence/lab04-*.png` (screenshots from the real browser)

**Interfaces:**
- Consumes: everything above.
- Produces: reproducible instructions and honest B1–B8 evidence.

- [ ] **Step 1: Install Flask and run the app**

Run: `python -m pip install -r requirements.txt`, then `python app.py` in the background.
Expected: server on <http://127.0.0.1:5000>; `/` and `/simulator` both return 200.

- [ ] **Step 2: Verify the real engine end-to-end**

Run the integration checks with the real executable (no mocks) for DC, AC, tran.
Expected: DC values match the fixture (`IC ≈ 1.417 mA`, `VCE ≈ 7.462 V`), AC returns
161 points, tran returns ≥ 2000 points, each log contains `Q2N3904`.

- [ ] **Step 3: UI critique/polish with Impeccable**

Run `npx impeccable install` from the repo root, choose OpenCode + project scope, then
load the `impeccable` skill and apply `critique` → `polish` to the running `/simulator`
page only. Keep calculations, plot data, units, and error states unchanged; do not
replace real charts with placeholder art. If the installer needs an interactive prompt
or fails, record `NOT RUN` with the reason and do a manual UI polish instead.

- [ ] **Step 4: Browser acceptance B1–B8**

Use the OpenCode Browser tool on the running app. Execute B1–B8 exactly as the spec
§5.11 table defines; capture desktop (~1280 px) and mobile (~390 px) screenshots for B8;
save evidence under `docs/evidence/`. Record `NOT RUN` for Playwright MCP with the reason
“ไม่ได้ติดตั้ง Playwright MCP; ใช้ OpenCode Browser ตามที่ผู้ใช้เลือก”.

- [ ] **Step 5: Write `docs/validation.md`**

Append a Lab 04 section with the table columns from the handout
(`Case | Method | Input | Expected/Reference | Observed | Evidence | Status`), plus
ngspice version (`ngspice-33`), model card name and source, the analytical assumptions,
the observed SPICE/analytical deltas, and limitations (no `init file` warning,
ngspice-33 `vp` quirk).

- [ ] **Step 6: Update `README.md`**

Add: what Lab 04 adds, ngspice install + `NGSPICE_EXE`, how to run the server, how to
reach `/simulator`, the reference values, the model source, the 2N3904-vs-analytical
BF difference, and the tested environment (Windows, Python 3.12.7, ngspice-33).

- [ ] **Step 7: Final verification and push**

Run: `python -m unittest -v` → all tests PASS. Re-open both pages once more.
Then:

```bash
git add README.md docs/validation.md docs/evidence
git commit -m "docs: record Lab 04 validation and run steps"
git push origin main
```

- [ ] **Step 8: Report the commit SHA and how to reproduce**

Print `git rev-parse HEAD` and the exact steps a classmate needs to run the app.
