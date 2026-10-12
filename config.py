"""All tunable values in one place. Edit here, not in the control code."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# ---- sensors (ids without the 28- prefix) ----
HOT_ID = "000000cb986b"      # water block probe
COLD_ID = ""                 # chamber cold-side probe; "" until probe #2 works

# ---- setpoints and hard limits ----
TARGET_HOT = 55.0            # deg C default setpoint
SETPOINT_MIN, SETPOINT_MAX = 30.0, 60.0   # remote setpoints are clamped to this range
MAX_HOT = 65.0               # hard cutoff -> FAULT
WATER_MIN = 200              # raw ADS1115; dry read ~45. Dip in water, pick a value between
FLOW_FACTOR = 7.5            # pulses/s per L/min (YF-S201). Check your sensor's datasheet
MIN_FLOW_LMIN = 0.2          # below this counts as "no flow" (calibrate with the real loop)
FLOW_GRACE_S = float(os.environ.get("MD_GRACE", "10"))            # seconds after Start before no-flow can trip
NOFLOW_STRIKES = 3           # consecutive low-flow samples before FAULT
SENSOR_FAIL_STRIKES = 3      # consecutive failed sensor reads before FAULT

# ---- output duty (0-1) ----
PUMP_DUTY = 0.8
PELTIER_DUTY = 0.3           # keep low until you have measured the current (see docs/WIRING.md)
FAN_DUTY = 1.0
HEATER_DUTY = 0.6
PWM_HZ = 1000

# ---- GPIO (BCM) ----
PIN_PUMP, PIN_PELTIER, PIN_HEATER, PIN_FAN, PIN_FLOW = 18, 13, 12, 19, 17

# ---- runtime ----
LOOP_S = float(os.environ.get("MD_LOOP_S", "2"))
PORT = 8000
LOG_FILE = os.path.join(BASE, "logs", "md_log.csv")
API_TOKEN = os.environ.get("MD_TOKEN", "")
AUTO_START = os.environ.get("MD_AUTO_START", "0") == "1"
SIMULATE = os.environ.get("MD_SIMULATE", "0") == "1"   # fake hardware, for laptop testing
if SIMULATE and not API_TOKEN:
    API_TOKEN = "test"
