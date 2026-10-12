"""Usage: python3 scripts/pwm_test.py <gpio> <duty 0-1> <seconds>"""
import sys, time
from gpiozero import PWMOutputDevice

pin = int(sys.argv[1])
duty = float(sys.argv[2])
secs = float(sys.argv[3]) if len(sys.argv) > 3 else 5

dev = PWMOutputDevice(pin)
try:
    dev.value = duty
    print(f"GPIO{pin} at {duty*100:.0f}% for {secs}s")
    time.sleep(secs)
finally:
    dev.off()
    print("off")
