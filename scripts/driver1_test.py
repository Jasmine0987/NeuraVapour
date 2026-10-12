from gpiozero import LED
from time import sleep

pump_pin = LED(18)
peltier_pin = LED(13)

while True:
    pump_pin.on(); peltier_pin.on(); sleep(1)
    pump_pin.off(); peltier_pin.off(); sleep(1)
