"""Drive every output pin low. Run this if anything looks wrong."""
from gpiozero import OutputDevice
for p in (18, 13, 12, 19):
    OutputDevice(p, initial_value=False).close()
print("all outputs off")
