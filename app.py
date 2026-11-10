import re

from flask import Flask, render_template, request

from bjt import BiasInputs, analyze

app = Flask(__name__)

DEFAULTS = {
    "vcc": "12",
    "r1": "47k",
    "r2": "10k",
    "rc": "2.2k",
    "re": "1k",
    "beta": "150",
    "vbe": "0.7",
}

RESISTANCE_KEYS = ("r1", "r2", "rc", "re")
NUMBER_KEYS = ("vcc", "beta", "vbe")

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


def build_inputs(form) -> BiasInputs:
    values = {}
    for key in RESISTANCE_KEYS:
        values[key] = parse_resistance(form.get(key, ""))
    for key in NUMBER_KEYS:
        values[key] = parse_number(form.get(key, ""))
    return BiasInputs(**values)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", raw=DEFAULTS, result=None, error=None)


if __name__ == "__main__":
    app.run(debug=True)
