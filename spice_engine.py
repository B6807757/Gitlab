"""ngspice adapter for the Lab 04 CE voltage-divider reference circuit.

The module only knows how to turn validated numbers into a netlist, run
ngspice in batch mode, and read its text log. It never invents results.
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


MODEL_NAME = "Q2N3904"

# Published 2N3904 card (mfg=Philips) from the LTspice Standard.bjt library:
# https://ltwiki.org/index.php?title=Standard.bjt
MODEL_CARD = (
    ".model Q2N3904 NPN(IS=1E-14 VAF=100 BF=300 IKF=0.4 XTB=1.5 BR=4\n"
    "+ CJC=4E-12 CJE=8E-12 RB=20 RC=0.1 RE=0.1 TR=250E-9 TF=350E-12\n"
    "+ ITF=1 VTF=2 XTF=3)"
)

MODEL_SOURCE = "LTspice Standard.bjt (mfg=Philips), https://ltwiki.org/index.php?title=Standard.bjt"

ANALYSIS_LABELS = {"dc": "DC (.op)", "ac": "AC (.ac)", "tran": "Transient (.tran)"}


class SpiceError(Exception):
    """Base class for every simulation failure the UI may show."""


class SpiceEngineNotFound(SpiceError):
    """The ngspice executable could not be located."""


class SpiceRunError(SpiceError):
    """ngspice was found but the run failed, timed out, or produced no log."""


class SpiceParseError(SpiceError):
    """The ngspice log does not contain the expected numeric tables."""


@dataclass(frozen=True)
class Circuit:
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    rl: float
    cin: float
    cout: float


@dataclass(frozen=True)
class Source:
    amplitude_v: float
    frequency_hz: float


@dataclass(frozen=True)
class DcResult:
    vb: float
    ve: float
    vc: float
    vce: float
    ic: float
    log: str
    netlist: str
    duration_s: float
    engine_version: str


_CIRCUIT_FIELDS = (
    ("vcc", "VCC", 100.0),
    ("r1", "R1", 1e9),
    ("r2", "R2", 1e9),
    ("rc", "RC", 1e9),
    ("re", "RE", 1e9),
    ("rl", "RL", 1e9),
    ("cin", "CIN", 1e9),
    ("cout", "COUT", 1e9),
)


def _fmt(value: float) -> str:
    return format(float(value), ".10g")


def validate_circuit(circuit: Circuit) -> None:
    for field, label, upper in _CIRCUIT_FIELDS:
        value = getattr(circuit, field)
        if not math.isfinite(value):
            raise ValueError(f"{label} ต้องเป็นจำนวนจริง")
        if value <= 0:
            raise ValueError(f"{label} ต้องมากกว่า 0")
        if value > upper:
            raise ValueError(f"{label} ต้องไม่เกิน {_fmt(upper)}")


def validate_source(source: Source) -> None:
    amp = source.amplitude_v
    freq = source.frequency_hz
    if not math.isfinite(amp) or not math.isfinite(freq):
        raise ValueError("แอมพลิจูดและความถี่ต้องเป็นจำนวนจริง")
    if amp <= 0 or amp > 1.0:
        raise ValueError("แอมพลิจูดต้องมากกว่า 0 และไม่เกิน 1 V peak")
    if freq < 10 or freq > 100e3:
        raise ValueError("ความถี่ต้องอยู่ระหว่าง 10 Hz ถึง 100 kHz")


def tran_timing(frequency_hz: float) -> tuple[float, float]:
    """Return (step_s, stop_s) for a 5 ms or three-cycle window."""
    stop = min(max(5e-3, 3.0 / frequency_hz), 0.2)
    step = min(stop / 2000.0, 1.0 / (50.0 * frequency_hz))
    return step, stop


def build_netlist(circuit: Circuit, source: Source, analysis: str) -> str:
    validate_circuit(circuit)
    validate_source(source)

    lines = [
        "* ENG29 2121 Lab 04 - CE voltage-divider reference",
        f"VCC 1 0 DC {_fmt(circuit.vcc)}",
        f"R1 1 2 {_fmt(circuit.r1)}",
        f"R2 2 0 {_fmt(circuit.r2)}",
        f"RC 1 3 {_fmt(circuit.rc)}",
        f"RE 4 0 {_fmt(circuit.re)}",
        f"Q1 3 2 4 {MODEL_NAME}",
        f"CIN 5 2 {_fmt(circuit.cin)}",
        f"COUT 3 6 {_fmt(circuit.cout)}",
        f"RL 6 0 {_fmt(circuit.rl)}",
        f"VIN 5 0 DC 0 AC 1 SIN(0 {_fmt(source.amplitude_v)} {_fmt(source.frequency_hz)})",
        MODEL_CARD,
    ]

    if analysis == "dc":
        lines.append(".op")
    elif analysis == "ac":
        lines.extend(
            [
                ".ac dec 20 1 100meg",
                ".print ac vm(5) vm(6)",
                ".print ac vp(5) vp(6)",
            ]
        )
    elif analysis == "tran":
        step, stop = tran_timing(source.frequency_hz)
        lines.extend([f".tran {_fmt(step)} {_fmt(stop)}", ".print tran v(5) v(6)"])
    else:
        raise ValueError(f"ไม่รู้จัก analysis: {analysis}")

    lines.append(".end")
    return "\n".join(lines) + "\n"


def find_engine(explicit: str | None = None) -> str:
    if explicit:
        path = Path(explicit)
        if path.is_file():
            return str(path)
        raise SpiceEngineNotFound(
            f"ไม่พบ ngspice ที่ {explicit} — ตั้งค่า NGSPICE_EXE ให้ชี้ไปที่ ngspice.exe"
        )

    env_path = os.environ.get("NGSPICE_EXE")
    if env_path:
        path = Path(env_path)
        if path.is_file():
            return str(path)
        raise SpiceEngineNotFound(
            f"NGSPICE_EXE ชี้ไปที่ {env_path} แต่ไม่พบไฟล์ — แก้ค่าให้ถูกต้อง"
        )

    found = shutil.which("ngspice")
    if found:
        return found

    local = os.environ.get("LOCALAPPDATA")
    if local:
        known = Path(local) / "Programs" / "ngspice" / "ngspice-33-w7" / "ngspice.exe"
        if known.is_file():
            return str(known)

    raise SpiceEngineNotFound(
        "ไม่พบ ngspice — ติดตั้ง ngspice แล้วเพิ่มลง PATH หรือตั้งค่า NGSPICE_EXE "
        "ให้ชี้ไปที่ ngspice.exe"
    )


def engine_version(exe: str) -> str:
    match = re.search(r"ngspice[-_]?(\d+(?:\.\d+)*)", exe)
    return f"ngspice-{match.group(1)}" if match else "unknown"


_NODE_RE = re.compile(r"^\s*V\((\d+)\)\s+(-?\d+(?:\.\d+)?[eE][+-]?\d+)\s*$")
_Q1_RE = re.compile(r"^\s*device\s+q1\b", re.IGNORECASE)
_DEVICE_RE = re.compile(r"^\s*device\b", re.IGNORECASE)
_IC_RE = re.compile(r"^\s*ic\s+(\S+)\s*$")


def _tail(text: str, limit: int = 600) -> str:
    text = (text or "").strip()
    return text[-limit:]


def _invoke(netlist: str, exe: str, timeout: float) -> str:
    with tempfile.TemporaryDirectory(prefix="lab04-ngspice-") as workdir:
        netlist_path = Path(workdir) / "circuit.cir"
        log_path = Path(workdir) / "run.log"
        netlist_path.write_text(netlist, encoding="ascii")

        try:
            completed = subprocess.run(
                [exe, "-b", "-o", "run.log", "circuit.cir"],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise SpiceRunError(
                f"ngspice ใช้เวลาเกิน {timeout:g} วินาที จึงหยุดการจำลอง"
            ) from exc
        except OSError as exc:
            raise SpiceRunError(f"เรียก ngspice ไม่สำเร็จ: {exc}") from exc

        if completed.returncode != 0:
            detail = _tail(completed.stderr) or _tail(completed.stdout) or "ไม่มีข้อความจาก ngspice"
            raise SpiceRunError(
                f"ngspice จบด้วยรหัส {completed.returncode}: {detail}"
            )

        if not log_path.is_file():
            raise SpiceRunError("ngspice ไม่ได้สร้าง run.log")

        log = log_path.read_text(encoding="utf-8", errors="replace")
        if not log.strip():
            raise SpiceRunError("ngspice log ว่างเปล่า — ไม่มีผลการจำลอง")
        return log


def parse_dc(
    log: str, netlist: str, duration_s: float, engine_version_text: str
) -> DcResult:
    nodes: dict[int, float] = {}
    ic: float | None = None
    in_q1 = False

    for line in log.splitlines():
        node = _NODE_RE.match(line)
        if node:
            nodes[int(node.group(1))] = float(node.group(2))
            continue
        if _Q1_RE.match(line):
            in_q1 = True
            continue
        if in_q1 and _DEVICE_RE.match(line):
            in_q1 = False
            continue
        if in_q1:
            current = _IC_RE.match(line)
            if current:
                try:
                    ic = float(current.group(1))
                except ValueError:
                    raise SpiceParseError("ค่า IC ของ q1 ไม่ใช่ตัวเลข") from None

    missing = [f"V({n})" for n in (1, 2, 3, 4) if n not in nodes]
    if missing:
        raise SpiceParseError("ไม่พบ " + ", ".join(missing) + " ใน ngspice log")
    if ic is None:
        raise SpiceParseError("ไม่พบกระแส IC ของ q1 ใน ngspice log")

    vb, vc, ve = nodes[2], nodes[3], nodes[4]
    values = (vb, ve, vc, vb - ve, vc - ve, ic)
    if not all(math.isfinite(value) for value in values):
        raise SpiceParseError("ngspice คืนค่าที่ไม่ใช่จำนวนจริง")

    return DcResult(
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vc - ve,
        ic=ic,
        log=log,
        netlist=netlist,
        duration_s=duration_s,
        engine_version=engine_version_text,
    )


def run_dc(
    circuit: Circuit,
    source: Source,
    *,
    exe: str | None = None,
    timeout: float = 20.0,
) -> DcResult:
    netlist = build_netlist(circuit, source, "dc")
    resolved = find_engine(exe)
    started = time.perf_counter()
    log = _invoke(netlist, resolved, timeout)
    duration = time.perf_counter() - started
    return parse_dc(log, netlist, duration, engine_version(resolved))
