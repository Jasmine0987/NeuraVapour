"""Heater at low duty with a hard temperature cutoff. Run only with the pump circulating water."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gpiozero import PWMOutputDevice
from w1thermsensor import W1ThermSensor, Sensor
import config

LIMIT = 55.0
DUTY = 0.3
RUN_SECONDS = 120

hot = W1ThermSensor(Sensor.DS18B20, config.HOT_ID)
heater = PWMOutputDevice(config.PIN_HEATER)
start = time.time()
try:
    heater.value = DUTY
    while time.time() - start < RUN_SECONDS:
        t = hot.get_temperature()
        print(f"hot: {t:.1f} C")
        if t >= LIMIT:
            print("LIMIT reached, heater off")
            break
        time.sleep(2)
finally:
    heater.off()
