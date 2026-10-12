# Wiring

## Power (12V side never touches Pi GPIO)
- 12V adapter **+** -> fuse -> Driver 1 **12V** and Driver 2 **12V**
- 12V adapter **-** -> Driver 1 **GND**, Driver 2 **GND**, and the shared ground with the Pi GND
- **Single power source (optional):** also feed the 12V into a 12V->5V buck converter (LM2596), set it to ~5.1 V *before* connecting the Pi, and power the Pi from it. Don't power the Pi from the L298D's 5V pin. Use a **12V 5A** adapter

## Loads
| Driver terminals | Load |
|---|---|
| Driver 1 OUT1 / OUT2 | Water pump |
| Driver 1 OUT3 / OUT4 | Peltier (polarity matters) |
| Driver 2 OUT1 / OUT2 | Resistor bank |
| Driver 2 OUT3 / OUT4 | Cooling fan |

## Control
- Pi 3.3V -> IN1 and IN3 on both drivers; Pi GND -> IN2 and IN4 on both
- GPIO18 -> Driver 1 ENA (pump), GPIO13 -> Driver 1 ENB (Peltier)
- GPIO12 -> Driver 2 ENA (resistors), GPIO19 -> Driver 2 ENB (fan)
- 10k pull-down from each EN pin to GND

## Sensors
- DS18B20 x2: Red -> 3.3V, Black -> GND, Yellow -> GPIO4, 4.7k between Yellow and 3.3V
- Flow sensor: Red -> 5V, Black -> GND, Yellow -> GPIO17 (voltage divider if the signal is 5V)
- ADS1115: VDD -> 3.3V, GND -> GND, SCL -> GPIO3, SDA -> GPIO2
- Sound sensor: `+` -> 3.3V, `G` -> GND, `AO` -> ADS1115 A0
- Water level sensor: `+` -> 3.3V, `-` -> GND, `S` -> ADS1115 A1

## Water loop
Pump -> flow sensor -> water block -> hot syringe (in/out stubs) -> pump inlet.
Vapor: hot syringe tip -> PTFE filter -> cold syringe resting on the Peltier cold face.
Heat: resistors -> heat sink -> water block -> water. The Peltier hot face has its own heat sink and fan.

## Current limits (read before raising any duty)
- An L298D channel is rated about 2 A and drops about 2 V, so loads see roughly 10 V, not 12 V.
- A TEC1-12706 can draw 4-6 A. PWM at 30% lowers the *average* current, but each on-pulse still carries the full current, so the driver can still be overloaded. Measure the real current. If it is above ~2 A, move the Peltier to a logic-level MOSFET module or a BTS7960 driver (it takes the same PWM signal from GPIO13).
- Resistor bank: keep 12 / R under 2 A, so R of about 6 ohm or more.
- The 3 A adapter is too small for everything at once; use 12V 5A.
