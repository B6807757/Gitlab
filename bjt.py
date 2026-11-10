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


def solve_linear_system(a: list[list[float]], b: list[float]) -> list[float]:
    n = len(a)
    m = [list(row) + [b[i]] for i, row in enumerate(a)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            raise ValueError("ระบบสมการไม่มีคำตอบเฉพาะ")
        m[col], m[pivot] = m[pivot], m[col]
        pv = m[col][col]
        for r in range(col + 1, n):
            f = m[r][col] / pv
            if f:
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]

    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = m[r][n] - sum(m[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s / m[r][r]
    return x


def solve_nodal(inputs: BiasInputs) -> dict[str, float]:
    beta = inputs.beta
    a = [
        [1.0 / inputs.r1 + 1.0 / inputs.r2, 0.0, 1.0 / beta],
        [0.0, -1.0 / inputs.rc, -1.0],
        [1.0 / inputs.re, 0.0, -(beta + 1.0) / beta],
    ]
    b = [inputs.vcc / inputs.r1, -inputs.vcc / inputs.rc, inputs.vbe / inputs.re]

    vb, vc, ic = solve_linear_system(a, b)
    ib = ic / beta
    ie = ic + ib
    ve = vb - inputs.vbe
    vce = vc - ve
    return {"ib": ib, "ic": ic, "ie": ie, "vb": vb, "ve": ve, "vc": vc, "vce": vce}


def relative_difference(a: dict[str, float], b: dict[str, float]) -> float:
    worst = 0.0
    for key in a.keys() & b.keys():
        worst = max(worst, abs(a[key] - b[key]) / max(abs(a[key]), 1e-12))
    return worst


VCE_SAT_V = 0.2
LOW_HEADROOM_V = 1.0


@dataclass(frozen=True)
class BiasResult:
    inputs: BiasInputs
    vbb: float
    rb: float
    ib: float
    ic: float
    ie: float
    vb: float
    ve: float
    vc: float
    vce: float
    region: str
    warnings: tuple[str, ...]
    ic_thevenin: float
    ic_nodal: float
    max_rel_diff: float
    ic_sat: float | None = None


def classify_region(vbb: float, vbe: float, vce: float) -> str:
    if vbb <= vbe:
        return "cutoff"
    if vce < VCE_SAT_V:
        return "saturation"
    return "active"


def analyze(inputs: BiasInputs) -> BiasResult:
    validate(inputs)
    vbb, rb = thevenin_equivalent(inputs)

    if vbb <= inputs.vbe:
        return BiasResult(
            inputs=inputs,
            vbb=vbb,
            rb=rb,
            ib=0.0,
            ic=0.0,
            ie=0.0,
            vb=vbb,
            ve=0.0,
            vc=inputs.vcc,
            vce=inputs.vcc,
            region="cutoff",
            warnings=("ทรานซิสเตอร์ตัดการทำงาน (VBB ≤ VBE): IC = 0 และ VCE = VCC",),
            ic_thevenin=0.0,
            ic_nodal=0.0,
            max_rel_diff=0.0,
        )

    thevenin = solve_thevenin(inputs)
    nodal = solve_nodal(inputs)
    region = classify_region(vbb, inputs.vbe, thevenin["vce"])

    warnings: list[str] = []
    ic_sat = None
    if region == "saturation":
        ic_sat = (inputs.vcc - VCE_SAT_V) / (inputs.rc + inputs.re)
        warnings.append(
            "Q-point อยู่ในโซนอิ่มตัว (VCE < 0.2 V): ค่าที่คำนวณไม่ใช่จุดทำงานจริง "
            "— ลด RC หรือเพิ่ม RE"
        )
    elif thevenin["vce"] < LOW_HEADROOM_V:
        warnings.append("VCE ต่ำกว่า 1.0 V: headroom เหลือน้อย ใกล้จะอิ่มตัว")

    return BiasResult(
        inputs=inputs,
        vbb=vbb,
        rb=rb,
        ib=thevenin["ib"],
        ic=thevenin["ic"],
        ie=thevenin["ie"],
        vb=thevenin["vb"],
        ve=thevenin["ve"],
        vc=thevenin["vc"],
        vce=thevenin["vce"],
        region=region,
        warnings=tuple(warnings),
        ic_thevenin=thevenin["ic"],
        ic_nodal=nodal["ic"],
        max_rel_diff=relative_difference(thevenin, nodal),
        ic_sat=ic_sat,
    )
