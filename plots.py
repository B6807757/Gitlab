"""Server-side SVG plots built only from parsed ngspice data."""

from __future__ import annotations

import math
from typing import Sequence

from spice_engine import AcPoint, TranPoint


_INK = "#17324a"
_MUTED = "#5b7185"
_GRID = "#dbe5ec"
_VIN = "#1f6fb2"
_VOUT = "#c0392b"


def _svg_open(width: int, height: int, label: str, title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{label}" class="plot">',
        f"<title>{title}</title>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
    ]


def _nice_ticks(low: float, high: float, count: int = 5) -> list[float]:
    if not math.isfinite(low) or not math.isfinite(high):
        return []
    if high <= low:
        return [low]
    raw = (high - low) / count
    magnitude = 10.0 ** math.floor(math.log10(raw))
    for factor in (1.0, 2.0, 2.5, 5.0, 10.0):
        step = factor * magnitude
        if step >= raw:
            break
    start = math.ceil(low / step) * step
    ticks: list[float] = []
    value = start
    while value <= high + step * 1e-9:
        ticks.append(round(value, 10))
        value += step
    return ticks


def _hz_label(value: float) -> str:
    if value >= 1e9:
        return f"{value / 1e9:g}G"
    if value >= 1e6:
        return f"{value / 1e6:g}M"
    if value >= 1e3:
        return f"{value / 1e3:g}k"
    return f"{value:g}"


def _number(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}g}"


def _axis(
    parts: list[str],
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    x_ticks: list[tuple[float, str]] = (),
    y_ticks: list[tuple[float, str]] = (),
) -> None:
    parts.append(
        f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x0:.1f}" y2="{y1:.1f}" '
        f'stroke="{_INK}" stroke-width="1"/>'
    )
    parts.append(
        f'<line x1="{x0:.1f}" y1="{y1:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
        f'stroke="{_INK}" stroke-width="1"/>'
    )
    for x, label in x_ticks:
        parts.append(
            f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y1 + 4:.1f}" '
            f'stroke="{_INK}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{y1 + 16:.1f}" text-anchor="middle" '
            f'font-size="10" fill="{_MUTED}">{label}</text>'
        )
    for y, label in y_ticks:
        parts.append(
            f'<line x1="{x0 - 4:.1f}" y1="{y:.1f}" x2="{x0:.1f}" y2="{y:.1f}" '
            f'stroke="{_INK}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x0 - 7:.1f}" y="{y + 3:.1f}" text-anchor="end" '
            f'font-size="10" fill="{_MUTED}">{label}</text>'
        )
        parts.append(
            f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}" '
            f'stroke="{_GRID}" stroke-width="1"/>'
        )


def _series(
    parts: list[str],
    points: Sequence[tuple[float, float]],
    color: str,
    *,
    width: float = 2.0,
) -> None:
    if not points:
        return
    coordinates = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    parts.append(
        f'<polyline fill="none" stroke="{color}" stroke-width="{width}" '
        f'points="{coordinates}"/>'
    )
    for x, y in points:
        parts.append(
            f'<circle data-point="1" cx="{x:.2f}" cy="{y:.2f}" r="1.6" '
            f'fill="{color}" opacity="0.55"/>'
        )


def _pad(low: float, high: float, minimum: float = 1e-9) -> tuple[float, float]:
    if high - low < minimum:
        centre = (high + low) / 2.0
        span = max(abs(centre) * 0.1, minimum)
        return centre - span, centre + span
    margin = (high - low) * 0.08
    return low - margin, high + margin


def bode_svg(
    points: Sequence[AcPoint], *, width: int = 760, height: int = 440
) -> str:
    if not points:
        raise ValueError("ไม่มีข้อมูล AC สำหรับวาดกราฟ")

    ordered = sorted(points, key=lambda point: point.frequency_hz)
    f_min = ordered[0].frequency_hz
    f_max = ordered[-1].frequency_hz
    if f_max <= f_min:
        f_max = f_min * 10.0

    left, right = 66.0, width - 20.0
    mag_top, mag_bottom = 42.0, height * 0.56
    phase_top, phase_bottom = height * 0.66, height - 38.0

    log_min, log_max = math.log10(f_min), math.log10(f_max)

    def x_of(frequency: float) -> float:
        ratio = (math.log10(frequency) - log_min) / (log_max - log_min)
        return left + ratio * (right - left)

    mag_values = [point.gain_db for point in ordered]
    mag_low, mag_high = _pad(min(mag_values), max(mag_values), 0.5)
    phase_values = [point.phase_deg for point in ordered]
    phase_low, phase_high = _pad(min(phase_values), max(phase_values), 5.0)

    def y_mag(value: float) -> float:
        ratio = (value - mag_low) / (mag_high - mag_low)
        return mag_bottom - ratio * (mag_bottom - mag_top)

    def y_phase(value: float) -> float:
        ratio = (value - phase_low) / (phase_high - phase_low)
        return phase_bottom - ratio * (phase_bottom - phase_top)

    decade_ticks: list[tuple[float, str]] = []
    for decade in range(math.floor(log_min), math.ceil(log_max) + 1):
        frequency = 10.0 ** decade
        if f_min <= frequency <= f_max:
            decade_ticks.append((x_of(frequency), _hz_label(frequency)))

    parts = _svg_open(width, height, "Bode plot จาก ngspice", "Bode plot")
    parts.append(
        f'<text x="{left:.0f}" y="20" font-size="13" font-weight="700" '
        f'fill="{_INK}">Bode · |Vout/Vin| และเฟส (ngspice)</text>'
    )

    _axis(
        parts,
        left,
        mag_top,
        right,
        mag_bottom,
        y_ticks=[(y_mag(v), _number(v, 3)) for v in _nice_ticks(mag_low, mag_high, 4)],
    )
    parts.append(
        f'<text x="14" y="{(mag_top + mag_bottom) / 2:.0f}" font-size="11" '
        f'fill="{_MUTED}" transform="rotate(-90 14 {(mag_top + mag_bottom) / 2:.0f})" '
        f'text-anchor="middle">ขนาด (dB)</text>'
    )

    _axis(
        parts,
        left,
        phase_top,
        right,
        phase_bottom,
        x_ticks=decade_ticks,
        y_ticks=[
            (y_phase(v), _number(v, 3)) for v in _nice_ticks(phase_low, phase_high, 4)
        ],
    )
    parts.append(
        f'<text x="14" y="{(phase_top + phase_bottom) / 2:.0f}" font-size="11" '
        f'fill="{_MUTED}" transform="rotate(-90 14 {(phase_top + phase_bottom) / 2:.0f})" '
        f'text-anchor="middle">เฟส (องศา)</text>'
    )
    parts.append(
        f'<text x="{(left + right) / 2:.0f}" y="{height - 8}" text-anchor="middle" '
        f'font-size="11" fill="{_MUTED}">ความถี่ (Hz)</text>'
    )

    _series(parts, [(x_of(p.frequency_hz), y_mag(p.gain_db)) for p in ordered], _VOUT)
    _series(
        parts,
        [(x_of(p.frequency_hz), y_phase(p.phase_deg)) for p in ordered],
        _VIN,
    )

    parts.append(
        f'<text x="{right:.0f}" y="{height - 8}" text-anchor="end" font-size="10" '
        f'fill="{_MUTED}">ngspice · Q2N3904 · {len(ordered)} points</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def transient_svg(
    points: Sequence[TranPoint], *, width: int = 760, height: int = 320
) -> str:
    if not points:
        raise ValueError("ไม่มีข้อมูล Transient สำหรับวาดกราฟ")

    ordered = sorted(points, key=lambda point: point.time_s)
    t_min, t_max = ordered[0].time_s, ordered[-1].time_s
    if t_max <= t_min:
        t_max = t_min + 1e-3

    left, right = 66.0, width - 20.0
    top, bottom = 40.0, height - 48.0

    values = [point.vin for point in ordered] + [point.vout for point in ordered]
    y_low, y_high = _pad(min(values), max(values), 1e-3)

    def x_of(time_s: float) -> float:
        ratio = (time_s - t_min) / (t_max - t_min)
        return left + ratio * (right - left)

    def y_of(value: float) -> float:
        ratio = (value - y_low) / (y_high - y_low)
        return bottom - ratio * (bottom - top)

    x_ticks = [
        (x_of(t_min + (t_max - t_min) * i / 5.0),
         _number((t_min + (t_max - t_min) * i / 5.0) * 1000.0, 3))
        for i in range(6)
    ]

    parts = _svg_open(width, height, "Transient waveform จาก ngspice", "Transient waveform")
    parts.append(
        f'<text x="{left:.0f}" y="20" font-size="13" font-weight="700" '
        f'fill="{_INK}">Transient · Vin และ Vout (ngspice)</text>'
    )

    _axis(
        parts,
        left,
        top,
        right,
        bottom,
        x_ticks=x_ticks,
        y_ticks=[(y_of(v), _number(v, 3)) for v in _nice_ticks(y_low, y_high, 5)],
    )
    parts.append(
        f'<text x="14" y="{(top + bottom) / 2:.0f}" font-size="11" fill="{_MUTED}" '
        f'text-anchor="middle" transform="rotate(-90 14 {(top + bottom) / 2:.0f})">'
        f"แรงดัน (V)</text>"
    )
    parts.append(
        f'<text x="{(left + right) / 2:.0f}" y="{height - 8}" text-anchor="middle" '
        f'font-size="11" fill="{_MUTED}">เวลา (ms)</text>'
    )

    _series(parts, [(x_of(p.time_s), y_of(p.vin)) for p in ordered], _VIN, width=1.5)
    _series(parts, [(x_of(p.time_s), y_of(p.vout)) for p in ordered], _VOUT, width=2.0)

    legend_x, legend_y = right - 96.0, top + 6.0
    parts.append(
        f'<line x1="{legend_x:.0f}" y1="{legend_y:.0f}" x2="{legend_x + 18:.0f}" '
        f'y2="{legend_y:.0f}" stroke="{_VIN}" stroke-width="2"/>'
    )
    parts.append(
        f'<text x="{legend_x + 24:.0f}" y="{legend_y + 4:.0f}" font-size="11" '
        f'fill="{_INK}">Vin</text>'
    )
    parts.append(
        f'<line x1="{legend_x:.0f}" y1="{legend_y + 18:.0f}" x2="{legend_x + 18:.0f}" '
        f'y2="{legend_y + 18:.0f}" stroke="{_VOUT}" stroke-width="2"/>'
    )
    parts.append(
        f'<text x="{legend_x + 24:.0f}" y="{legend_y + 22:.0f}" font-size="11" '
        f'fill="{_INK}">Vout</text>'
    )
    parts.append(
        f'<text x="{right:.0f}" y="{height - 8}" text-anchor="end" font-size="10" '
        f'fill="{_MUTED}">ngspice · Q2N3904 · {len(ordered)} points</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)
