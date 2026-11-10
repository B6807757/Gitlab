import math
from dataclasses import dataclass


@dataclass(frozen=True)
class BiasInputs:
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


_FIELD_LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
}


def validate(inputs: BiasInputs) -> None:
    for field, label in _FIELD_LABELS.items():
        if not math.isfinite(getattr(inputs, field)):
            raise ValueError(f"{label} ต้องเป็นจำนวนจริง")

    for field in ("vcc", "r1", "r2", "rc", "re"):
        if getattr(inputs, field) <= 0:
            raise ValueError(f"{_FIELD_LABELS[field]} ต้องมากกว่า 0")

    if inputs.beta < 1:
        raise ValueError("β ต้องไม่น้อยกว่า 1")

    if not 0 <= inputs.vbe < inputs.vcc:
        raise ValueError("VBE ต้องอยู่ระหว่าง 0 ถึง VCC")


def thevenin_equivalent(inputs: BiasInputs) -> tuple[float, float]:
    vbb = inputs.vcc * inputs.r2 / (inputs.r1 + inputs.r2)
    rb = 1.0 / (1.0 / inputs.r1 + 1.0 / inputs.r2)
    return vbb, rb


def solve_thevenin(inputs: BiasInputs) -> dict[str, float]:
    vbb, rb = thevenin_equivalent(inputs)
    ib = (vbb - inputs.vbe) / (rb + (1.0 + inputs.beta) * inputs.re)
    ic = inputs.beta * ib
    ie = (1.0 + inputs.beta) * ib
    ve = ie * inputs.re
    vc = inputs.vcc - ic * inputs.rc
    vb = ve + inputs.vbe
    vce = vc - ve
    return {"ib": ib, "ic": ic, "ie": ie, "vb": vb, "ve": ve, "vc": vc, "vce": vce}
