from gpiozero import LED
from time import sleep

resistor_pin = LED(12)
fan_pin = LED(19)

while True:
    resistor_pin.on(); fan_pin.on(); sleep(1)
    resistor_pin.off(); fan_pin.off(); sleep(1)
