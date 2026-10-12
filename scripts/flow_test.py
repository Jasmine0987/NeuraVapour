from gpiozero import Button
from signal import pause

flow = Button(17)
count = [0]

def tick():
    count[0] += 1
    print('pulses:', count[0])

flow.when_pressed = tick
pause()
