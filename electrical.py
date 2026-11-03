import math


def analyze_dc(voltage_v, resistance_ohm):
    if resistance_ohm == 0:
        raise ValueError("Resistance must not be zero.")

    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {"current_a": current_a, "power_w": power_w}


def analyze_solar_panel(
    irradiance_w_m2,
    panel_temp_c,
    panel_area_m2,
    voltage_v,
    current_a,
    rated_power_w,
    temp_coefficient_per_c=-0.004,
):
    values = {
        "irradiance": irradiance_w_m2,
        "panel temperature": panel_temp_c,
        "panel area": panel_area_m2,
        "voltage": voltage_v,
        "current": current_a,
        "rated power": rated_power_w,
        "temperature coefficient": temp_coefficient_per_c,
    }
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("All measurements must be finite numbers.")
    if irradiance_w_m2 <= 0 or panel_area_m2 <= 0 or rated_power_w <= 0:
        raise ValueError("Irradiance, panel area, and rated power must be positive.")
    if voltage_v < 0 or current_a < 0:
        raise ValueError("Voltage and current must not be negative.")

    output_power_w = voltage_v * current_a
    solar_input_power_w = irradiance_w_m2 * panel_area_m2
    efficiency_percent = output_power_w / solar_input_power_w * 100

    temperature_factor = max(0, 1 + temp_coefficient_per_c * (panel_temp_c - 25))
    expected_power_w = rated_power_w * (irradiance_w_m2 / 1000) * temperature_factor
    performance_ratio_percent = output_power_w / expected_power_w * 100 if expected_power_w else 0

    return {
        "output_power_w": output_power_w,
        "efficiency_percent": efficiency_percent,
        "expected_power_w": expected_power_w,
        "performance_ratio_percent": performance_ratio_percent,
    }


def main():
    print("Solar Panel Efficiency Tracker")
    print("Enter the current measurements and panel specifications.")

    measurements = {
        "irradiance_w_m2": float(input("Solar irradiance (W/m^2): ")),
        "panel_temp_c": float(input("Panel temperature (C): ")),
        "panel_area_m2": float(input("Panel area (m^2): ")),
        "voltage_v": float(input("Measured voltage (V): ")),
        "current_a": float(input("Measured current (A): ")),
        "rated_power_w": float(input("Rated panel power at STC (W): ")),
        "temp_coefficient_per_c": float(
            input("Power temperature coefficient per C (default -0.004): ") or -0.004
        ),
    }

    results = analyze_solar_panel(**measurements)
    print(f"\nMeasured output power: {results['output_power_w']:.2f} W")
    print(f"Panel conversion efficiency: {results['efficiency_percent']:.2f}%")
    print(f"Expected power at current conditions: {results['expected_power_w']:.2f} W")
    print(f"Performance ratio: {results['performance_ratio_percent']:.2f}%")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(f"Input error: {error}")
    