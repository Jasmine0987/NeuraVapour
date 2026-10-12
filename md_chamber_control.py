"""MD chamber controller + remote control page.

Safety interlocks (over-temp, no-flow, low water, sensor failure) run in the
controller loop on the Pi and do not depend on WiFi. The web page can only
Start, Stop, clear a fault, and change the setpoint within fixed limits.
"""
import csv, hmac, os, random, signal, sys, threading, time
from datetime import datetime
import config

OUTS = ("pump", "peltier", "heater", "fan")


class RealHW:
    def __init__(self):
        import board, busio
        from gpiozero import PWMOutputDevice, Button
        from w1thermsensor import W1ThermSensor, Sensor
        from adafruit_ads1x15.ads1115 import ADS1115
        from adafruit_ads1x15.analog_in import AnalogIn
        self.hot_s = W1ThermSensor(Sensor.DS18B20, config.HOT_ID)
        self.cold_s = W1ThermSensor(Sensor.DS18B20, config.COLD_ID) if config.COLD_ID else None
        ads = ADS1115(busio.I2C(board.SCL, board.SDA))
        self.sound_ch = AnalogIn(ads, 0)
        self.water_ch = AnalogIn(ads, 1)
        self._pulses = 0
        self.flow = Button(config.PIN_FLOW)
        self.flow.when_pressed = self._tick
        pins = dict(pump=config.PIN_PUMP, peltier=config.PIN_PELTIER,
                    heater=config.PIN_HEATER, fan=config.PIN_FAN)
        self.dev = {n: PWMOutputDevice(p, frequency=config.PWM_HZ) for n, p in pins.items()}

    def _tick(self):
        self._pulses += 1

    def take_pulses(self, dt):
        n, self._pulses = self._pulses, 0
        return n

    def read_temps(self):
        hot = self.hot_s.get_temperature()
        cold = self.cold_s.get_temperature() if self.cold_s else None
        return hot, cold

    def water(self):
        return self.water_ch.value

    def sound(self):
        return self.sound_ch.value

    def set(self, name, duty):
        self.dev[name].value = duty

    def all_off(self):
        for d in self.dev.values():
            d.off()


class SimHW:
    """Fake hardware so the page and interlocks can be tried on a laptop."""
    def __init__(self):
        self.t, self.c = 25.0, 22.0
        self.duty = {n: 0.0 for n in OUTS}
        self.flow_ok = True      # set False to simulate a blocked loop

    def take_pulses(self, dt):
        lmin = 2.5 * self.duty["pump"] if self.flow_ok else 0
        return int(lmin * config.FLOW_FACTOR * dt)

    def read_temps(self):
        self.t += self.duty["heater"] * 1.5 - 0.03 * (self.t - 25)
        return self.t, self.c

    def water(self):
        return 800

    def sound(self):
        return 100 + random.randint(0, 20)

    def set(self, name, duty):
        self.duty[name] = duty

    def all_off(self):
        for n in OUTS:
            self.duty[n] = 0.0


class Controller:
    def __init__(self, hw):
        self.hw = hw
        self.lock = threading.RLock()
        self.stop_evt = threading.Event()
        self.state, self.fault = "IDLE", ""
        self.target = config.TARGET_HOT
        self.started_at = 0.0
        self.noflow = self.sensor_fail = 0
        self.flow_ok = False
        self.duty = {n: 0.0 for n in OUTS}
        self.latest = {}
        os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
        self.logf = open(config.LOG_FILE, "a", newline="")
        self.log = csv.writer(self.logf)
        if self.logf.tell() == 0:
            self.log.writerow(["time", "state", "hot_C", "cold_C", "flow_Lmin", "sound",
                               "water", "target", "heater_duty", "peltier_duty"])

    # ---- outputs ----
    def _set(self, name, duty):
        self.duty[name] = duty
        self.hw.set(name, duty)

    def _all_off(self):
        self.hw.all_off()
        for n in OUTS:
            self.duty[n] = 0.0

    # ---- commands (called from the web page) ----
    def start(self):
        with self.lock:
            if self.state == "FAULT":
                return False, "clear the fault first"
            if self.state != "RUNNING":
                self.state, self.started_at = "RUNNING", time.time()
                self.noflow = self.sensor_fail = 0
                self.flow_ok = False
                self._set("pump", config.PUMP_DUTY)
                self._set("fan", config.FAN_DUTY)
            return True, "running"

    def stop(self):
        with self.lock:
            self._all_off()
            if self.state == "RUNNING":
                self.state = "IDLE"
            return True, "stopped"

    def clear_fault(self):
        with self.lock:
            if self.state == "FAULT":
                self.state, self.fault = "IDLE", ""
            return True, "cleared"

    def set_target(self, v):
        with self.lock:
            v = max(config.SETPOINT_MIN, min(config.SETPOINT_MAX, float(v)))
            self.target = v
            return True, v

    def shutdown(self):
        self.stop_evt.set()
        self._all_off()

    # ---- safety ----
    def _trip(self, reason):
        self._all_off()
        self.state, self.fault = "FAULT", reason
        print("FAULT:", reason, flush=True)

    # ---- control step ----
    def tick(self, dt):
        flow = self.hw.take_pulses(dt) / dt / config.FLOW_FACTOR
        try:
            hot, cold = self.hw.read_temps()
            water, sound = self.hw.water(), self.hw.sound()
            self.sensor_fail = 0
        except Exception as e:
            self.sensor_fail += 1
            print("sensor error:", e, flush=True)
            if self.state == "RUNNING" and self.sensor_fail >= config.SENSOR_FAIL_STRIKES:
                self._trip("sensor read failed")
            return

        if self.state == "RUNNING":
            if hot >= config.MAX_HOT:
                self._trip(f"over-temperature ({hot:.1f} C)")
            elif water < config.WATER_MIN:
                self._trip(f"water level low ({water})")
            else:
                if flow >= config.MIN_FLOW_LMIN:
                    self.flow_ok, self.noflow = True, 0
                else:
                    self.flow_ok = False
                    if time.time() - self.started_at > config.FLOW_GRACE_S:
                        self.noflow += 1
                        if self.noflow >= config.NOFLOW_STRIKES:
                            self._trip("no flow detected")
                if self.state == "RUNNING":
                    # heater and Peltier only run while water is confirmed moving
                    if self.flow_ok:
                        self._set("peltier", config.PELTIER_DUTY)
                        self._set("heater", config.HEATER_DUTY if hot < self.target else 0.0)
                    else:
                        self._set("peltier", 0.0)
                        self._set("heater", 0.0)

        self.latest = dict(time=datetime.now().isoformat(timespec="seconds"), hot=round(hot, 2),
                           cold=None if cold is None else round(cold, 2), flow=round(flow, 2),
                           water=water, sound=sound)
        if self.state == "RUNNING":
            self.log.writerow([self.latest["time"], self.state, self.latest["hot"],
                               "" if cold is None else self.latest["cold"], self.latest["flow"],
                               sound, water, self.target, self.duty["heater"], self.duty["peltier"]])
            self.logf.flush()

    def loop(self):
        last = time.time()
        while not self.stop_evt.is_set():
            self.stop_evt.wait(config.LOOP_S)
            now = time.time()
            dt, last = max(now - last, 0.1), now
            with self.lock:
                try:
                    self.tick(dt)
                except Exception as e:
                    self._trip(f"controller error: {e}")
        self._all_off()

    def snapshot(self):
        with self.lock:
            return dict(self.latest, state=self.state, fault=self.fault, target=self.target,
                        flow_ok=self.flow_ok, duty=dict(self.duty),
                        limits=[config.SETPOINT_MIN, config.SETPOINT_MAX], max_hot=config.MAX_HOT)


# ------------------------------------------------------------------ web
from flask import Flask, jsonify, request, Response

app = Flask(__name__)
ctl = None


def check_auth():
    """Returns an error response, or None if the request is allowed."""
    if not config.API_TOKEN:
        return jsonify(error="remote control disabled: set MD_TOKEN in .env"), 503
    if not hmac.compare_digest(request.headers.get("X-Token", ""), config.API_TOKEN):
        return jsonify(error="wrong token"), 401
    return None


@app.get("/")
def index():
    return Response(PAGE, mimetype="text/html")


@app.get("/api/status")
def api_status():
    return check_auth() or jsonify(ctl.snapshot())


def command(fn, *args):
    bad = check_auth()
    if bad:
        return bad
    ok, msg = fn(*args)
    return (jsonify(ok=True, msg=msg), 200) if ok else (jsonify(error=msg), 409)


@app.post("/api/start")
def api_start():
    return command(ctl.start)


@app.post("/api/stop")
def api_stop():
    return command(ctl.stop)


@app.post("/api/clear")
def api_clear():
    return command(ctl.clear_fault)


@app.post("/api/setpoint")
def api_setpoint():
    try:
        v = float((request.get_json(silent=True) or {})["value"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="send {\"value\": number}"), 400
    return command(ctl.set_target, v)


PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>MD Chamber</title>
<style>
:root{color-scheme:light dark;font-family:system-ui,sans-serif}
body{max-width:520px;margin:0 auto;padding:16px}
h1{font-size:1.2rem;margin:0 0 12px}
.card{border:1px solid #8884;border-radius:10px;padding:12px;margin-bottom:12px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.big{font-size:1.6rem;font-weight:600}.lbl{font-size:.75rem;opacity:.7}
button{font-size:1rem;padding:12px;border-radius:8px;border:1px solid #8886;width:100%}
.row{display:flex;gap:8px}.go{background:#2a7;color:#fff}.no{background:#c33;color:#fff}
#state{font-weight:700}.FAULT{color:#c33}.RUNNING{color:#2a7}
input[type=text]{width:100%;box-sizing:border-box;padding:8px}input[type=range]{width:100%}
#msg{color:#c33;min-height:1.2em}
</style></head><body>
<h1>MD Chamber</h1>
<div class="card"><span class="lbl">State</span> <span id="state">-</span><div id="fault" class="FAULT"></div></div>
<div class="card grid">
<div><div class="lbl">Water block</div><div class="big"><span id="hot">-</span> &deg;C</div></div>
<div><div class="lbl">Cold side</div><div class="big"><span id="cold">-</span> &deg;C</div></div>
<div><div class="lbl">Flow (L/min)</div><div class="big" id="flow">-</div></div>
<div><div class="lbl">Water level (raw)</div><div class="big" id="water">-</div></div>
</div>
<div class="card"><div class="lbl">Target water block temp: <b id="tv">-</b> &deg;C</div>
<input type="range" id="sp" step="1"></div>
<div class="row"><button class="go" onclick="cmd('start')">Start</button>
<button class="no" onclick="cmd('stop')">Stop</button></div>
<div class="row" style="margin-top:8px"><button onclick="cmd('clear')">Clear fault</button></div>
<p id="msg"></p>
<div class="card"><div class="lbl">Access token</div><input type="text" id="tok" autocomplete="off"></div>
<script>
const $=id=>document.getElementById(id);
let tok=localStorage.getItem('mdtok')||'';$('tok').value=tok;
$('tok').onchange=()=>{tok=$('tok').value;localStorage.setItem('mdtok',tok);poll()};
async function api(p,body){
  const r=await fetch(p,{method:body===undefined?'GET':'POST',
    headers:{'X-Token':tok,'Content-Type':'application/json'},
    body:body===undefined?undefined:JSON.stringify(body)});
  const j=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(j.error||r.status);return j}
async function cmd(c){try{await api('/api/'+c,{});$('msg').textContent=''}catch(e){$('msg').textContent=e.message}poll()}
$('sp').onchange=async()=>{try{await api('/api/setpoint',{value:+$('sp').value})}catch(e){$('msg').textContent=e.message}poll()};
$('sp').oninput=()=>{$('tv').textContent=$('sp').value};
function render(s){
  $('state').textContent=s.state;$('state').className=s.state;
  $('fault').textContent=s.fault||'';
  $('hot').textContent=s.hot??'-';$('cold').textContent=s.cold??'-';
  $('flow').textContent=s.flow??'-';$('water').textContent=s.water??'-';
  $('sp').min=s.limits[0];$('sp').max=s.limits[1];
  if(document.activeElement!==$('sp')){$('sp').value=s.target;$('tv').textContent=s.target}}
async function poll(){try{render(await api('/api/status'));$('msg').textContent=''}catch(e){$('msg').textContent=e.message}}
poll();setInterval(poll,2000);
</script></body></html>"""


def main():
    global ctl
    ctl = Controller(SimHW() if config.SIMULATE else RealHW())

    def bye(*_):
        ctl.shutdown()
        sys.exit(0)
    signal.signal(signal.SIGTERM, bye)
    signal.signal(signal.SIGINT, bye)

    threading.Thread(target=ctl.loop, daemon=True).start()
    if config.AUTO_START:
        print("AUTO_START on: starting run", flush=True)
        ctl.start()
    if not config.API_TOKEN:
        print("WARNING: MD_TOKEN not set, remote control disabled", flush=True)
    app.run(host="0.0.0.0", port=config.PORT, threaded=True)


if __name__ == "__main__":
    main()
