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


if __name__ == "__main__":
    app.run(debug=False)
