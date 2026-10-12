# Pi setup and test commands (Pi 3 B+)

Scripts live in `scripts/`. Pasting into nano over PuTTY flattens line breaks, so get files onto the Pi with `git clone` or `scp` instead.

## 1. Connect and enable interfaces
```
ssh jas1912@<pi-ip>
sudo raspi-config
```
Interface Options -> I2C on -> 1-Wire on -> Finish. The Pi reboots and PuTTY disconnects; that's normal.

## 2. Install libraries
```
sudo apt update
sudo apt install python3-pip python3-smbus i2c-tools python3-flask git -y
pip3 install adafruit-circuitpython-ads1x15 RPi.GPIO w1thermsensor gpiozero --break-system-packages
```

## 3. Detect the ADS1115 (expect 48 in the grid)
```
sudo i2cdetect -y 1
```

## 4. DS18B20 probes
```
ls /sys/bus/w1/devices/
cat /sys/bus/w1/devices/28-XXXXXXXXXXXX/w1_slave
```
`crc=... YES` is a good read; `t=31000` is 31.0 C. If probes don't show up:
```
sudo modprobe -r w1_therm
sudo modprobe -r w1_gpio
sudo modprobe w1_gpio
sudo modprobe w1_therm
ls /sys/bus/w1/devices/
```

## 5. Sensor checks
```
python3 scripts/probes.py      # ids + temperatures
python3 scripts/st.py          # sound (A0) + water level (A1); clap, dip in water
python3 scripts/flow_test.py   # spin the wheel, or tap a jumper GPIO17 <-> GND
```
`AttributeError: ... no attribute 'P0'` means you used `ADS.P0`; use the channel number (`AnalogIn(ads, 0)`).

## 6. Get the project onto the Pi
```
git clone https://github.com/YOUR-USERNAME/hydrocool-md-prototype.git
cd hydrocool-md-prototype
```

## 7. Safe shutdown (always, before cutting power or rewiring)
```
sudo shutdown now
```
Wait for the green LED to stop flashing, then unplug.

## Terminal basics
| Task | Command |
|---|---|
| List files | `ls -la` |
| Edit a file | `nano file` (save Ctrl+O, Enter; exit Ctrl+X) |
| Stop a script | Ctrl+C |
