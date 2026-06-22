import requests
from config import ARM_IP


class RobotArm:

    def __init__(self):

        print("🤖 RobotArm initialized")

        # Positional servos — 0 to 270, center at 135
        self.servo_angles = {
            "elbow":        135,
            "wrist_ud":     135,
            "wrist_rotate": 135,
            "claw":         135
        }

        # Continuous motors — tracked as pulse values directly
        # 307 = CONT_STOP, 102 = full reverse, 512 = full forward
        self.motor_pulse = {
            "base":     307,
            "shoulder": 307
        }

        # Speed for legacy stop/home use
        self.motor_speed = {
            "base":     0,
            "shoulder": 0
        }


    def send(self, active_joints: list):

        payload = {
            "servo_angles": self.servo_angles,
            "motor_speed":  self.motor_speed,
            "motor_pulse":  self.motor_pulse,
            "active":       active_joints
        }

        url = f"http://{ARM_IP}/update"

        print("\n📡 SENDING TO ESP32")
        print("➡ Active joints:", active_joints)
        print("📦 PAYLOAD:", payload)

        try:
            response = requests.post(url, json=payload, timeout=0.3)
            print("✅ ESP32 RESPONSE:", response.text)
        except Exception as e:
            print("❌ ESP32 ERROR:", e)


    # =========================
    # SERVO CONTROL — positional
    # =========================
    def move_servo(self, name, delta):

        print(f"🎯 move_servo() → {name}  Δ{delta}")

        if name not in self.servo_angles:
            print("⚠ UNKNOWN SERVO:", name)
            return

        self.servo_angles[name] = max(0, min(270, self.servo_angles[name] + delta))
        print("📊 ANGLES:", self.servo_angles)

        self.send(active_joints=[name])


    def set_servo(self, name, angle):

        print(f"🎯 set_servo() → {name} = {angle}")

        if name not in self.servo_angles:
            print("⚠ UNKNOWN SERVO:", name)
            return

        self.servo_angles[name] = max(0, min(270, angle))

        self.send(active_joints=[name])


    # =========================
    # MOTOR NUDGE — increments pulse directly each interval
    # delta: positive = forward, negative = reverse
    # Each call moves the motor by a fixed pulse step and holds there
    # =========================
    def nudge_motor(self, name, delta):

        print(f"⚙ nudge_motor() → {name}  Δ{delta}")

        if name not in self.motor_pulse:
            print("⚠ UNKNOWN MOTOR:", name)
            return

        # Clamp within hardware pulse range
        self.motor_pulse[name] = max(102, min(512, self.motor_pulse[name] + delta))
        print("📊 PULSE:", self.motor_pulse)

        self.send(active_joints=[name])


    def stop_motor(self, name):

        print(f"🛑 stop_motor() → {name}")

        if name not in self.motor_pulse:
            return

        self.motor_pulse[name] = 307  # CONT_STOP
        self.motor_speed[name] = 0

        self.send(active_joints=[name])


    # =========================
    # LEGACY — set_motor kept for stop/home compatibility
    # =========================
    def set_motor(self, name, speed):

        if name not in self.motor_speed:
            return

        self.motor_speed[name] = max(-100, min(100, speed))
        self.motor_pulse[name] = 307  # reset to stop
        self.send(active_joints=[name])


    # =========================
    # HOME — centers everything
    # =========================
    def home(self):

        print("🏠 home() — centering all joints")

        for k in self.servo_angles:
            self.servo_angles[k] = 135

        for k in self.motor_pulse:
            self.motor_pulse[k] = 307

        for k in self.motor_speed:
            self.motor_speed[k] = 0

        self.send(active_joints=["base", "shoulder", "elbow", "wrist_ud", "wrist_rotate", "claw"])


    # =========================
    # STOP — stops motors only
    # =========================
    def stop_all_motors(self):

        print("🛑 stop_all_motors()")

        for k in self.motor_pulse:
            self.motor_pulse[k] = 307

        for k in self.motor_speed:
            self.motor_speed[k] = 0

        self.send(active_joints=["base", "shoulder"])