# Test order

Do these in order. Stop and fix anything that fails before moving on.

## A. Logic only (12V OFF, loads disconnected)
- [ ] `python3 scripts/driver1_test.py`: ENA/ENB on driver 1 swing 0 V <-> 3.3 V on a multimeter (GPIO18, GPIO13)
- [ ] `python3 scripts/driver2_test.py`: same on driver 2 (GPIO12, GPIO19)
- [ ] `python3 scripts/probes.py` shows **two** `28-...` probes. Warm one in your hand; note which id is the water block (`HOT_ID`) and which is cold side (`COLD_ID`), then put them in `config.py`
- [ ] `python3 scripts/st.py`: dry water reading ~45; dip it and note the wet value. Set `WATER_MIN` in `config.py` between the two

## B. Before applying 12V (no code)
- [ ] Fuse inline on the 12V+ line
- [ ] Multimeter continuity: no beep between 12V and GND on either driver
- [ ] Resistor bank is 5-15 ohm. Bank current = 12 / R and one L298D channel is rated 2 A, so aim for **6 ohm or more**
- [ ] All GNDs joined at one point (Pi, 12V supply, both drivers, sensors)
- [ ] 10k resistor from each EN pin to GND (heater and Peltier stay off while the Pi boots)
- [ ] Pump submerged or primed (never run it dry)

## C. PWM with 12V, one device at a time
`python3 scripts/pwm_test.py <gpio> <duty> <seconds>`

| Device | Command |
|---|---|
| Pump | `python3 scripts/pwm_test.py 18 0.5 5` |
| Fan | `python3 scripts/pwm_test.py 19 0.5 5` |
| Peltier | `python3 scripts/pwm_test.py 13 0.3 10` |
| Resistor bank | `python3 scripts/pwm_test.py 12 0.3 10` |

- [ ] Pump moves water and fan spins **before** you test the Peltier or heater
- [ ] Raise duty gradually: 0.3, 0.5, 0.8, 1.0
- [ ] **Measure current** on the 12V line while the Peltier runs (see WIRING.md, current limits)

## D. Peltier polarity
- [ ] Run 30% for 10 s with its heat sink and fan attached. The cold face must face the chamber wall; if not, swap the two wires on OUT3/OUT4
- [ ] Never run it more than a few seconds without the hot-side heat sink and fan

## E. Heater with safety cutoff
- [ ] Pump circulating, then `python3 scripts/heater_test.py` (30% duty, cuts at 55 C, stops after 120 s)

## F. Flow calibration
- [ ] `python3 scripts/flow_test.py` with the pump running; confirm pulses arrive
- [ ] After step G starts a run, read `flow_Lmin` in `logs/md_log.csv`. Set `MIN_FLOW_LMIN` in `config.py` to about half of your normal running flow

## G. Controller and remote page, Start pressed by hand
```
bash deploy/install.sh        # installs the service, prints your token
```
- [ ] Open `http://<pi-ip>:8000`, paste the token, press Start
- [ ] Pinch or kink the tubing: within about 10-16 s the state must go **FAULT: no flow detected** and all outputs must switch off
- [ ] Press Stop mid-run: all outputs off
- [ ] Lift the water level sensor out: FAULT (low water)

## H. Leak test (no code)
- [ ] Full loop with plain tap water, pump running 15+ minutes, watch every joint and the chamber seal. Sealant needs ~24 h to cure before it gets water

## I. Autonomous start
Only after A-H pass: set `MD_AUTO_START=1` in `.env`, then `sudo systemctl restart mdchamber`. The rig then starts a run whenever it gets power.
