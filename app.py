import re

from flask import Flask, render_template, request

from bjt import (
    BiasInputs,
    EmitterInputs,
    FixedInputs,
    ModeResult,
    agreement_ok,
    analyze,
    analyze_emitter,
    analyze_fixed,
    format_current,
    format_resistance,
    format_voltage,
)
from plots import bode_svg, transient_svg
from spice_engine import (
    MODEL_NAME,
    MODEL_SOURCE,
    AcResult,
    Circuit,
    DcResult,
    Source,
    SpiceEngineNotFound,
    SpiceError,
    TranResult,
    engine_version,
    find_engine,
    run_ac,
    run_dc,
    run_tran,
    validate_circuit,
    validate_source,
)

app = Flask(__name__)
app.jinja_env.globals.update(
    agreement_ok=agreement_ok,
    format_current=format_current,
    format_resistance=format_resistance,
    format_voltage=format_voltage,
)

DEFAULTS = {
    "vcc": "12",
    "r1": "47k",
    "r2": "10k",
    "rc": "2.2k",
    "re": "1k",
    "beta": "150",
    "vbe": "0.7",
}

FIXED_DEFAULTS = {
    "vcc": "12",
    "rb": "1M",
    "rc": "2.2k",
    "beta": "100",
    "vbe": "0.70",
}

EMITTER_DEFAULTS = {
    "vcc": "12",
    "rb": "1M",
    "rc": "2.2k",
    "re": "1k",
    "beta": "100",
    "vbe": "0.70",
}

SIM_DEFAULTS = {
    "vcc": "12",
    "r1": "100k",
    "r2": "22k",
    "rc": "2.2k",
    "re": "1k",
    "rl": "10k",
    "cin": "10u",
    "cout": "10u",
    "amp_mv": "10",
    "freq": "1k",
    "beta": "150",
    "vbe": "0.70",
}

SIM_ANALYSIS = {"dc": "DC (.op)", "ac": "AC (.ac)", "tran": "Transient (.tran)"}

MODE_DEFS = {
    "divider": {
        "label": "Voltage Divider Bias",
        "hint": "วงจรไบแอสแบบแบ่งแรงดัน · หน่วย V, Ω และ β (ไม่มีหน่วย)",
        "resistance_fields": ("r1", "r2", "rc", "re"),
        "number_fields": ("vcc", "beta", "vbe"),
        "defaults": DEFAULTS,
    },
    "fixed": {
        "label": "Fixed Bias",
        "hint": "ไบแอสฐานด้วยตัวต้านทานตัวเดียว · หน่วย V, Ω และ β (ไม่มีหน่วย)",
        "resistance_fields": ("rb", "rc"),
        "number_fields": ("vcc", "beta", "vbe"),
        "defaults": FIXED_DEFAULTS,
    },
    "emitter": {
        "label": "Emitter Bias",
        "hint": "ไบแอสฐานด้วย RB และมี RE ป้อนกลับที่อิมิตเตอร์ · หน่วย V, Ω และ β (ไม่มีหน่วย)",
        "resistance_fields": ("rb", "rc", "re"),
        "number_fields": ("vcc", "beta", "vbe"),
        "defaults": EMITTER_DEFAULTS,
    },
}

MODE_ORDER = ("divider", "fixed", "emitter")

_RESISTANCE_RE = re.compile(r"^([0-9]*\.?[0-9]+)\s*([kKM])?\s*(Ω|ohm)?$")

_NUMBER_ERROR = "กรุณากรอกเป็นตัวเลข"


def parse_number(text: str) -> float:
    value = (text or "").strip()
    if not value:
        raise ValueError(_NUMBER_ERROR)
    try:
        return float(value)
    except ValueError:
        raise ValueError(_NUMBER_ERROR) from None


def parse_resistance(text: str) -> float:
    value = (text or "").strip()
    match = _RESISTANCE_RE.match(value)
    if not match:
        raise ValueError(_NUMBER_ERROR)
    prefix = {"k": 1e3, "K": 1e3, "M": 1e6}.get(match.group(2) or "", 1.0)
    return float(match.group(1)) * prefix


_CAPACITANCE_RE = re.compile(r"^([0-9]*\.?[0-9]+)\s*([pnuµmμ])?\s*[Ff]?$")


def parse_capacitance(text: str) -> float:
    value = (text or "").strip()
    match = _CAPACITANCE_RE.match(value)
    if not match:
        raise ValueError("กรุณากรอกค่าความจุเป็นตัวเลข เช่น 10u หรือ 100n")
    prefix = {
        "p": 1e-12,
        "n": 1e-9,
        "u": 1e-6,
        "µ": 1e-6,
        "μ": 1e-6,
        "m": 1e-3,
    }.get(match.group(2) or "", 1.0)
    return float(match.group(1)) * prefix


def build_mode_inputs(mode: str, form):
    spec = MODE_DEFS[mode]
    values = {}
    for key in spec["resistance_fields"]:
        values[key] = parse_resistance(form.get(key, ""))
    for key in spec["number_fields"]:
        values[key] = parse_number(form.get(key, ""))

    if mode == "divider":
        return BiasInputs(**values)
    if mode == "fixed":
        return FixedInputs(**values)
    if mode == "emitter":
        return EmitterInputs(**values)
    raise ValueError(f"ไม่รู้จักโหมดที่เลือก: {mode}")


def build_inputs(form) -> BiasInputs:
    return build_mode_inputs("divider", form)


DEFAULT_MODE_INPUTS = {
    mode: build_mode_inputs(mode, spec["defaults"]) for mode, spec in MODE_DEFS.items()
}
DEFAULT_INPUTS = DEFAULT_MODE_INPUTS["divider"]


def _solve(mode: str, inputs):
    if mode == "divider":
        return analyze(inputs)
    if mode == "fixed":
        return ModeResult(inputs=inputs, **analyze_fixed(inputs))
    return ModeResult(inputs=inputs, **analyze_emitter(inputs))


def run_simulation(circuit: Circuit, source: Source, analysis: str):
    if analysis == "dc":
        return run_dc(circuit, source)
    if analysis == "ac":
        return run_ac(circuit, source)
    if analysis == "tran":
        return run_tran(circuit, source)
    raise ValueError(f"ไม่รู้จัก analysis: {analysis}")


def _engine_status() -> tuple[str | None, str]:
    try:
        path = find_engine()
    except SpiceEngineNotFound:
        return None, "unknown"
    return path, engine_version(path)


def _hz_text(value: float | None) -> str:
    if value is None:
        return "not determined in sweep range"
    if value >= 1e6:
        return f"{value / 1e6:.3g} MHz"
    if value >= 1e3:
        return f"{value / 1e3:.3g} kHz"
    return f"{value:.3g} Hz"


def _dc_rows(result: DcResult, analytical) -> list[dict[str, str]]:
    specs = (
        ("VB", "vb", "V", 1.0),
        ("VE", "ve", "V", 1.0),
        ("VC", "vc", "V", 1.0),
        ("VCE", "vce", "V", 1.0),
        ("IC", "ic", "mA", 1000.0),
    )
    rows = []
    for label, attribute, unit, scale in specs:
        spice = getattr(result, attribute) * scale
        row = {
            "label": label,
            "unit": unit,
            "spice": f"{spice:.3f} {unit}",
            "reference": "—",
            "delta": "—",
            "percent": "—",
        }
        if analytical is not None:
            reference = getattr(analytical, attribute) * scale
            delta = spice - reference
            row["reference"] = f"{reference:.3f} {unit}"
            row["delta"] = f"{delta:+.3f} {unit}"
            row["percent"] = f"{delta / reference * 100:+.1f}%" if reference else "—"
        rows.append(row)
    return rows


def _render_simulator(**overrides):
    context = {
        "raw": SIM_DEFAULTS,
        "result": None,
        "analysis": None,
        "analysis_label": None,
        "svg": None,
        "dc_rows": None,
        "analytical": None,
        "analytical_error": None,
        "ac_summary": None,
        "tran_summary": None,
        "error": None,
        "model_name": MODEL_NAME,
        "model_source": MODEL_SOURCE,
    }
    path, version = _engine_status()
    context["engine_path"] = path
    context["engine_version"] = version
    context.update(overrides)
    return render_template("simulator.html", **context)


@app.after_request
def _disable_cache(response):
    if request.endpoint == "index":
        response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        mode = (request.args.get("mode") or "divider").strip().lower()
        if mode not in MODE_DEFS:
            return (
                render_template(
                    "index.html",
                    mode=None,
                    mode_label=None,
                    mode_defs=MODE_DEFS,
                    mode_order=MODE_ORDER,
                    raw=None,
                    result=None,
                    error=f"ไม่รู้จักโหมดที่เลือก: {mode}",
                    diagram=None,
                ),
                400,
            )
        spec = MODE_DEFS[mode]
        return render_template(
            "index.html",
            mode=mode,
            mode_label=spec["label"],
            mode_defs=MODE_DEFS,
            mode_order=MODE_ORDER,
            raw=spec["defaults"],
            result=None,
            error=None,
            diagram=DEFAULT_MODE_INPUTS[mode],
        )

    mode = (request.form.get("mode") or "").strip().lower()
    if mode not in MODE_DEFS:
        if mode:
            error = f"ไม่รู้จักโหมดที่เลือก: {mode}"
        else:
            error = "ไม่ได้ระบุโหมด (mode)"
        return (
            render_template(
                "index.html",
                mode=None,
                mode_label=None,
                mode_defs=MODE_DEFS,
                mode_order=MODE_ORDER,
                raw=None,
                result=None,
                error=error,
                diagram=None,
            ),
            400,
        )

    spec = MODE_DEFS[mode]
    raw = {key: request.form.get(key, "") for key in spec["defaults"]}
    try:
        result = _solve(mode, build_mode_inputs(mode, raw))
        error = None
    except ValueError as exc:
        result = None
        error = f"{spec['label']}: {exc}"

    diagram = result.inputs if result is not None else DEFAULT_MODE_INPUTS[mode]
    return render_template(
        "index.html",
        mode=mode,
        mode_label=spec["label"],
        mode_defs=MODE_DEFS,
        mode_order=MODE_ORDER,
        raw=raw,
        result=result,
        error=error,
        diagram=diagram,
    )


@app.get("/simulator")
def simulator_form():
    return _render_simulator()


@app.post("/simulator")
def simulator_run():
    analysis = (request.form.get("analysis") or "").strip().lower()
    raw = {key: request.form.get(key, "") for key in SIM_DEFAULTS}

    if analysis not in SIM_ANALYSIS:
        return (
            _render_simulator(raw=raw, error="ไม่ได้ระบุโหมดวิเคราะห์ (dc / ac / tran)"),
            400,
        )

    try:
        circuit = Circuit(
            vcc=parse_number(raw["vcc"]),
            r1=parse_resistance(raw["r1"]),
            r2=parse_resistance(raw["r2"]),
            rc=parse_resistance(raw["rc"]),
            re=parse_resistance(raw["re"]),
            rl=parse_resistance(raw["rl"]),
            cin=parse_capacitance(raw["cin"]),
            cout=parse_capacitance(raw["cout"]),
        )
        source = Source(
            amplitude_v=parse_number(raw["amp_mv"]) / 1000.0,
            frequency_hz=parse_resistance(raw["freq"]),
        )
        validate_circuit(circuit)
        validate_source(source)
    except ValueError as exc:
        return _render_simulator(
            raw=raw,
            analysis=analysis,
            analysis_label=SIM_ANALYSIS[analysis],
            error=f"ข้อมูลไม่ถูกต้อง: {exc}",
        )

    try:
        result = run_simulation(circuit, source, analysis)
    except SpiceError as exc:
        return _render_simulator(
            raw=raw,
            analysis=analysis,
            analysis_label=SIM_ANALYSIS[analysis],
            error=str(exc),
        )

    analytical = None
    analytical_error = None
    dc_rows = None
    if analysis == "dc":
        try:
            analytical = analyze(
                BiasInputs(
                    circuit.vcc,
                    circuit.r1,
                    circuit.r2,
                    circuit.rc,
                    circuit.re,
                    parse_number(raw["beta"]),
                    parse_number(raw["vbe"]),
                )
            )
        except ValueError as exc:
            analytical_error = f"คำนวณ Analytical ไม่ได้: {exc}"
        dc_rows = _dc_rows(result, analytical)

    svg = None
    ac_summary = None
    tran_summary = None

    if isinstance(result, AcResult):
        svg = bode_svg(result.points)
        point = result.gain_1khz
        ac_summary = {
            "gain": f"{point.gain:.3f}" if point else "—",
            "gain_db": f"{point.gain_db:.2f}" if point else "—",
            "phase": f"{point.phase_deg:.1f}" if point else "—",
            "f_low": _hz_text(result.f_low_hz),
            "f_high": _hz_text(result.f_high_hz),
        }
    elif isinstance(result, TranResult):
        svg = transient_svg(result.points)
        tran_summary = {
            "vin_pp": f"{result.vin_pp * 1000:.2f}",
            "vout_pp": f"{result.vout_pp * 1000:.2f}",
            "inverted": "กลับเฟส (~180°)" if result.inverted else "ไม่กลับเฟส",
            "window": f"{result.stop_s * 1000:.2f}",
            "step": f"{result.step_s * 1e6:.2f}",
        }

    return _render_simulator(
        raw=raw,
        result=result,
        analysis=analysis,
        analysis_label=SIM_ANALYSIS[analysis],
        svg=svg,
        dc_rows=dc_rows,
        analytical=analytical,
        analytical_error=analytical_error,
        ac_summary=ac_summary,
        tran_summary=tran_summary,
        engine_version=result.engine_version,
    )


if __name__ == "__main__":
    app.run(debug=False)
