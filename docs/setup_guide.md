# Setup Guide

## Prerequisites

- Arduino IDE 2.x with ESP32 board support installed
  - Board manager URL: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
  - Install: **esp32 by Espressif Systems** (tested on v2.x)
- Python 3.10+
- A 2.4 GHz Wi-Fi network

---

## Arduino Libraries (install via Library Manager)

| Library | Author |
|---|---|
| Adafruit PWM Servo Driver Library | Adafruit |
| ArduinoJson | Benoit Blanchon |

---

## Step 1 — Flash the Arm Controller

1. Open `firmware/esp32_arm_controller/esp32_arm_controller.ino` in Arduino IDE.
2. Edit the Wi-Fi credentials at the top of the file:
   ```cpp
   const char* ssid     = "YOUR_SSID";
   const char* password = "YOUR_PASSWORD";
   ```
3. Select board: **ESP32 Dev Module**
4. Upload speed: 115200 baud
5. Flash the board.
6. Open Serial Monitor at 115200 baud — note the IP address printed after `IP:`.
7. Set that IP as `ARM_IP` in `server/config.py`.

---

## Step 2 — Flash the ESP32-CAM

1. Open `firmware/esp32_cam_streamer/esp32_cam_streamer.ino`.
2. Edit Wi-Fi credentials the same way.
3. **Before connecting USB:** bridge IO0 to GND to enter bootloader mode.
4. Select board: **AI Thinker ESP32-CAM**
5. Flash. Remove the IO0–GND bridge, then press the reset button.
6. Open Serial Monitor — note the IP printed after `Connected — stream at:`.
7. Set that IP as `CAMERA_IP` in `server/config.py`.

---

## Step 3 — Python Server

```bash
# From the repo root
pip install -r requirements.txt

cd server
python app.py
```

The server starts on `http://0.0.0.0:5000`.

---

## Step 4 — Open the GUI

Navigate to `http://localhost:5000` in any browser on the same machine.

To control from another device on the same network, use `http://<laptop-IP>:5000`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Motors don't move | Wrong `ARM_IP` | Re-check Serial Monitor output, update `config.py` |
| Camera shows "RECONNECTING" | Wrong `CAMERA_IP` | Re-check cam Serial Monitor output |
| ESP32 resets under load | PSU undersized | Use ≥ 5V 10A supply for the motors |
| Shoulder motors fight each other | Mirroring inverted | Swap `LEFT_SHOULDER` and `RIGHT_SHOULDER` channel numbers |
| Jittery servo at rest | Deadband too small | Increase `DEAD_BAND` in the `.ino` |
| 5 GHz network | ESP32 is 2.4 GHz only | Switch to a 2.4 GHz SSID |
