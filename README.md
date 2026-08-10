# Reflowster

Reflowster is a Textual-based control app for a solder reflow oven built from a toaster oven. It reads solder reflow profiles from JSON files, monitors temperature via a MAX31855 thermocouple amplifier, and controls an SSR using PID and time-proportional control.

## Requirements

- Python 3.13
- `requirements.txt` contains hardware and UI dependencies, including `textual`, `textual-plotext`, `gpiozero`, and `adafruit-circuitpython-max31855`.
- A supported single-board computer or microcontroller board with a compatible `board` pin definition for Adafruit Blinka.

## Installation

Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

## Usage

Run the application with the SSR relay pin and MAX31855 chip-select pin:

```bash
python reflowster.py --relay-pin 10 --cs-pin D5
```

- `--relay-pin`: GPIO pin number controlling the SSR.
- `--cs-pin`: `board` pin name for the MAX31855 CS line.

Once running, select a reflow profile from the `reflow_profiles/` directory and use the UI controls to start, stop, or change profiles.

## PID Autotuning

Generate tuned PID parameters automatically and save them to `pid_parameters.json` using:

```bash
python pid_autotune.py --relay-pin 10 --cs-pin D5 --setpoint 180
```

- `--setpoint`: target temperature for autotuning in °C.
- `--hysteresis`: temperature deadband around the setpoint.
- `--min-cycles`: number of relay on/off cycles to observe.

The script will create or overwrite `pid_parameters.json` with the tuned `Kp`, `Ki`, and `Kd` values.

## Configuration

- Save PID tuning values in `pid_parameters.json` as a JSON object with `Kp`, `Ki`, and `Kd` keys.
- Reflow profile JSON files should include a `points` array with `[time, temperature]` points and an optional `safety.max_temp_c` cutoff.

## Notes

This project relies on Adafruit Blinka and board detection, so it is intended to run on a supported hardware platform rather than a generic Windows desktop environment.
