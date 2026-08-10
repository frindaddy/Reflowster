"""Standalone PID autotune helper for Reflowster.

This script performs a relay autotune procedure by cycling the SSR heater on and off
around a target temperature setpoint. It saves the resulting PID tuning parameters to
pid_parameters.json in the repository root.
"""

import argparse
import json
import time
from pathlib import Path

import board
import digitalio

from hw.max31855 import MAX31855
from hw.ssr import SSR

JSON_OUTPUT_PATH = Path(__file__).resolve().parent / "pid_parameters.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Autotune PID parameters for Reflowster.")
    parser.add_argument("--relay-pin", type=int, default=17, help="GPIO pin number for the SSR relay")
    parser.add_argument("--cs-pin", default="D5", help="Board pin name used for MAX31855 CS")
    parser.add_argument("--setpoint", type=float, default=180.0, help="Target temperature for autotuning (°C)")
    parser.add_argument("--hysteresis", type=float, default=5.0, help="Temperature hysteresis around the setpoint (°C)")
    parser.add_argument("--min-cycles", type=int, default=5, help="Minimum number of relay cycles to observe")
    parser.add_argument("--sample-interval", type=float, default=1.0, help="Seconds between temperature samples")
    parser.add_argument("--timeout", type=float, default=1800.0, help="Maximum time allowed for autotuning in seconds")
    return parser.parse_args()


def resolve_cs_pin(pin_name: str) -> digitalio.DigitalInOut:
    try:
        board_pin = getattr(board, pin_name)
    except AttributeError as error:
        raise SystemExit(f"Unknown board pin '{pin_name}'.") from error
    return digitalio.DigitalInOut(board_pin)


def compute_pid_parameters(periods: list[float], temperature_readings: list[float]) -> dict[str, float]:
    if len(periods) < 1:
        raise ValueError("Not enough relay oscillation periods to compute PID parameters.")

    avg_period = sum(periods) / len(periods)
    peak = max(temperature_readings)
    trough = min(temperature_readings)
    amplitude = (peak - trough) / 2.0

    if amplitude <= 0.0:
        raise ValueError("Measured temperature amplitude is zero or negative.")

    relay_output_span = 100.0
    ku = 4.0 * relay_output_span / (3.141592653589793 * amplitude)
    tu = avg_period

    return {
        "Kp": round(0.6 * ku, 4),
        "Ki": round(1.2 * ku / tu, 4),
        "Kd": round(0.075 * ku * tu, 4),
        "Ku": round(ku, 4),
        "Tu": round(tu, 4),
    }


def save_parameters(parameters: dict[str, float], output_path: Path) -> None:
    output_path.write_text(json.dumps(parameters, indent=2) + "\n", encoding="utf-8")
    print(f"Saved PID parameters to {output_path}")
    print("Generated PID parameters:")
    print(json.dumps(parameters, indent=2))


def run_autotune(
    relay_pin: int,
    cs_pin: digitalio.DigitalInOut,
    setpoint: float,
    hysteresis: float,
    min_cycles: int,
    sample_interval: float,
    timeout: float,
) -> dict[str, float]:
    sensor = MAX31855(spi=board.SPI(), cs=cs_pin)
    ssr = SSR(relay_pin)
    ssr.off()

    start_time = time.time()
    toggle_times: list[float] = []
    readings: list[float] = []
    current_state = False

    print(
        f"Starting PID autotune with setpoint={setpoint}°C, hysteresis=±{hysteresis}°C, min_cycles={min_cycles}"
    )
    print("This procedure will run until the requested number of cycles has been observed.")

    try:
        while True:
            now = time.time()
            if now - start_time > timeout:
                raise TimeoutError("Autotune timed out before completing the required number of cycles.")

            temperature = sensor.read_temperature()
            if temperature is None:
                print("Warning: temperature sensor returned no reading.")
            else:
                readings.append(temperature)
                print(f"{temperature:.2f}°C | relay={'ON' if current_state else 'OFF'} | elapsed={now-start_time:.1f}s")

            if temperature is not None:
                if current_state and temperature >= setpoint + hysteresis:
                    ssr.off()
                    current_state = False
                    toggle_time = time.time()
                    toggle_times.append(toggle_time)
                    print(f"Relay turned OFF at {temperature:.2f}°C")
                elif not current_state and temperature <= setpoint - hysteresis:
                    ssr.on()
                    current_state = True
                    toggle_time = time.time()
                    toggle_times.append(toggle_time)
                    print(f"Relay turned ON at {temperature:.2f}°C")

            if len(toggle_times) >= (min_cycles * 2) + 1:
                full_periods = [
                    toggle_times[i + 2] - toggle_times[i]
                    for i in range(len(toggle_times) - 2)
                ]
                print(f"Measured {len(full_periods)} full cycle periods. Finishing autotune.")
                break

            sleep_time = sample_interval - ((time.time() - now) % sample_interval)
            if sleep_time > 0:
                time.sleep(min(sleep_time, sample_interval))

    finally:
        ssr.off()
        print("SSR turned off.")

    return compute_pid_parameters(full_periods, readings)


def main() -> int:
    args = parse_args()
    cs_pin = resolve_cs_pin(args.cs_pin)

    try:
        parameters = run_autotune(
            relay_pin=args.relay_pin,
            cs_pin=cs_pin,
            setpoint=args.setpoint,
            hysteresis=args.hysteresis,
            min_cycles=args.min_cycles,
            sample_interval=args.sample_interval,
            timeout=args.timeout,
        )
    except Exception as error:
        print(f"Autotune failed: {error}")
        return 1

    save_parameters(parameters, JSON_OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
