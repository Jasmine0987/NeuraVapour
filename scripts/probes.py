from w1thermsensor import W1ThermSensor

for s in W1ThermSensor.get_available_sensors():
    print(s.id, round(s.get_temperature(), 2), "C")
