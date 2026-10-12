import time, board, busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)
sound = AnalogIn(ads, 0)
water = AnalogIn(ads, 1)

while True:
    print('sound:', sound.value, 'water:', water.value)
    time.sleep(1)
