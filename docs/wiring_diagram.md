# Wiring Diagram

## Power Distribution

```
5V 20A PSU
    ├── (+) → PCA9685 V+ rail  (motor power)
    ├── (+) → PCA9685 VCC      (logic, via jumper)
    └── GND → Common ground (PSU, PCA9685, ESP32, all motors)
```

> ⚠️ The ESP32 dev board is powered separately via USB from the laptop running the Flask server. Do **not** power it from the 5V PSU unless you add a proper 3.3V regulator.

---

## ESP32 Dev Board → PCA9685

| ESP32 Pin | PCA9685 Pin | Signal |
|---|---|---|
| GPIO 21 | SDA | I2C Data |
| GPIO 22 | SCL | I2C Clock |
| 3.3V | VCC | Logic power |
| GND | GND | Ground |

PCA9685 I2C address: `0x40` (default, all address pins low)

---

## PCA9685 → Motors

| Channel | Motor / Servo | Signal Wire Color (typical) |
|---|---|---|
| 0 | Base — REV Continuous | Orange |
| 1 | Left Shoulder — REV Continuous | Orange |
| 2 | Right Shoulder — REV Continuous | Orange |
| 3 | Elbow — MG996R | Orange |
| 4 | Wrist Up/Down — MG996R | Orange |
| 5 | Wrist Rotation — Micro Servo | Orange |
| 6 | Claw — Micro Servo | Orange |

All servo power (red/brown) connects to the PCA9685 V+ rail from the PSU.

---

## ESP32-CAM

The ESP32-CAM is powered and programmed separately. During flashing, connect IO0 to GND to enter bootloader mode.

| ESP32-CAM Pin | Connection |
|---|---|
| 5V | 5V from PSU or USB adapter |
| GND | Common ground |
| IO0 | GND during flash only, float during run |

The CAM connects to Wi-Fi independently and streams to the IP set in `server/config.py → CAMERA_IP`.

---

## Notes

- Use a **common ground** between the PSU, ESP32, and PCA9685 — floating grounds cause erratic motor behavior.
- REV Continuous motors accept standard RC PWM (50 Hz). The PCA9685 is configured to 50 Hz in firmware.
- Keep motor wires away from I2C signal wires to minimize noise.
