import time
import requests
from config import ARM_IP

# =========================
# DIRECT SENDER
# Bypasses Flask and sends straight to ESP32
# =========================

CONT_STOP = 307

def send(servo_angles, motor_pulse, active_joints):
    payload = {
        "servo_angles": servo_angles,
        "motor_speed":  {"base": 0, "shoulder": 0},
        "motor_pulse":  motor_pulse,
        "active":       active_joints
    }
    try:
        requests.post(f"http://{ARM_IP}/update", json=payload, timeout=1.0)
    except Exception as e:
        print(f"❌ Send error: {e}")


# =========================
# STATE TRACKING
# =========================
state = {
    "servo_angles": {
        "elbow":        135,
        "wrist_ud":     135,
        "wrist_rotate": 135,
        "claw":         135
    },
    "motor_pulse": {
        "base":     CONT_STOP,
        "shoulder": CONT_STOP
    }
}


# =========================
# MOVEMENT PRIMITIVES
# =========================

def set_servo(name, angle, delay=0.02):
    """Move a positional servo to an absolute angle (0-270)."""
    angle = max(0, min(270, angle))
    state["servo_angles"][name] = angle
    send(state["servo_angles"], state["motor_pulse"], [name])
    time.sleep(delay)


def sweep_servo(name, start, end, steps=20, step_delay=0.05):
    """Smoothly sweep a positional servo from start to end angle."""
    print(f"  → sweep {name}: {start}° → {end}°")
    step_size = (end - start) / steps
    for i in range(steps + 1):
        angle = int(start + step_size * i)
        set_servo(name, angle, delay=step_delay)


def nudge_motor(name, pulse, duration, stop_delay=0.3):
    """Run a continuous motor at a given pulse for a set duration then stop."""
    pulse = max(102, min(512, pulse))
    state["motor_pulse"][name] = pulse
    send(state["servo_angles"], state["motor_pulse"], [name])
    time.sleep(duration)
    state["motor_pulse"][name] = CONT_STOP
    send(state["servo_angles"], state["motor_pulse"], [name])
    time.sleep(stop_delay)


def home_all(delay=0.5):
    """Send all joints to center position."""
    print("  → HOME ALL")
    for k in state["servo_angles"]:
        state["servo_angles"][k] = 135
    for k in state["motor_pulse"]:
        state["motor_pulse"][k] = CONT_STOP
    send(state["servo_angles"], state["motor_pulse"],
         ["base", "shoulder", "elbow", "wrist_ud", "wrist_rotate", "claw"])
    time.sleep(delay)


def pause(seconds):
    print(f"  ⏸  pause {seconds}s")
    time.sleep(seconds)


# =========================
# SEQUENCES
# =========================

def sequence_wave():
    """
    Simple wave — raises the elbow up and down twice.
    Good for quick demo.
    """
    print("\n▶ SEQUENCE: WAVE")

    home_all()

    for _ in range(2):
        sweep_servo("elbow", 135, 220, steps=15, step_delay=0.04)
        sweep_servo("elbow", 220, 100, steps=25, step_delay=0.04)
        sweep_servo("elbow", 100, 135, steps=15, step_delay=0.04)
        pause(0.3)

    home_all()
    print("✅ Wave done")


def sequence_scan():
    """
    Base rotates left and right like a radar scan.
    """
    print("\n▶ SEQUENCE: SCAN")

    home_all()

    # Rotate base left
    nudge_motor("base", 240, duration=1.2)
    pause(0.4)

    # Rotate base right (past center to right)
    nudge_motor("base", 370, duration=2.4)
    pause(0.4)

    # Back to center
    nudge_motor("base", 240, duration=1.2)
    pause(0.3)

    home_all()
    print("✅ Scan done")


def sequence_pickup():
    """
    Simulates picking something up:
    lower shoulder → open claw → close claw → raise shoulder.
    """
    print("\n▶ SEQUENCE: PICKUP SIMULATION")

    home_all()

    # Lower shoulder
    print("  → Lower shoulder")
    nudge_motor("shoulder", 240, duration=1.0)
    pause(0.3)

    # Open claw
    print("  → Open claw")
    sweep_servo("claw", 135, 240, steps=15, step_delay=0.04)
    pause(0.4)

    # Close claw (grab)
    print("  → Close claw (grab)")
    sweep_servo("claw", 240, 60, steps=25, step_delay=0.04)
    pause(0.5)

    # Raise shoulder
    print("  → Raise shoulder")
    nudge_motor("shoulder", 370, duration=1.0)
    pause(0.3)

    # Rotate base to deposit
    print("  → Rotate to deposit")
    nudge_motor("base", 370, duration=1.2)
    pause(0.4)

    # Release claw
    print("  → Release claw")
    sweep_servo("claw", 60, 220, steps=20, step_delay=0.04)
    pause(0.4)

    home_all()
    print("✅ Pickup done")


def sequence_wrist_display():
    """
    Sweeps wrist rotation and wrist UD for a fluid showcase movement.
    """
    print("\n▶ SEQUENCE: WRIST DISPLAY")

    home_all()

    # Raise elbow slightly
    sweep_servo("elbow", 135, 190, steps=10, step_delay=0.04)

    # Sweep wrist rotation left to right
    sweep_servo("wrist_rotate", 135, 40,  steps=20, step_delay=0.04)
    sweep_servo("wrist_rotate", 40,  230, steps=30, step_delay=0.04)
    sweep_servo("wrist_rotate", 230, 135, steps=20, step_delay=0.04)

    # Wrist UD up and down
    sweep_servo("wrist_ud", 135, 220, steps=15, step_delay=0.04)
    sweep_servo("wrist_ud", 220, 60,  steps=25, step_delay=0.04)
    sweep_servo("wrist_ud", 60,  135, steps=15, step_delay=0.04)

    home_all()
    print("✅ Wrist display done")


def sequence_full_showcase():
    """
    Full showcase — runs all sequences back to back with pauses.
    Best for live demos.
    """
    print("\n▶▶ FULL SHOWCASE STARTING ◀◀")
    print("Press Ctrl+C to stop at any time\n")

    sequence_scan()
    pause(1.0)

    sequence_wave()
    pause(1.0)

    sequence_wrist_display()
    pause(1.0)

    sequence_pickup()
    pause(1.0)

    home_all(delay=1.0)
    print("\n✅ FULL SHOWCASE COMPLETE")


def sequence_idle():
    """
    Gentle idle loop — subtle movements to show the arm is alive.
    Runs forever until Ctrl+C.
    """
    print("\n▶ IDLE LOOP — press Ctrl+C to stop")
    home_all()

    idle_positions = [
        # (servo, angle)
        ("wrist_rotate", 160),
        ("wrist_rotate", 110),
        ("wrist_ud",     155),
        ("wrist_ud",     115),
        ("elbow",        150),
        ("elbow",        120),
        ("wrist_rotate", 135),
        ("wrist_ud",     135),
        ("elbow",        135),
    ]

    try:
        while True:
            for name, angle in idle_positions:
                sweep_servo(name, state["servo_angles"][name], angle, steps=20, step_delay=0.06)
                pause(0.5)
    except KeyboardInterrupt:
        print("\n⛔ Idle stopped")
        home_all()


# =========================
# MENU
# =========================

def main():
    print("=" * 45)
    print("   ARM-6 SEQUENCE CONTROLLER")
    print(f"   Target: {ARM_IP}")
    print("=" * 45)
    print()
    print("  1  →  Wave")
    print("  2  →  Scan (base rotation)")
    print("  3  →  Pickup simulation")
    print("  4  →  Wrist display")
    print("  5  →  Full showcase (all sequences)")
    print("  6  →  Idle loop (runs forever)")
    print("  0  →  Home all joints")
    print()

    choice = input("Select sequence: ").strip()

    sequences = {
        "1": sequence_wave,
        "2": sequence_scan,
        "3": sequence_pickup,
        "4": sequence_wrist_display,
        "5": sequence_full_showcase,
        "6": sequence_idle,
        "0": home_all,
    }

    if choice in sequences:
        try:
            sequences[choice]()
        except KeyboardInterrupt:
            print("\n⛔ Interrupted — homing arm")
            home_all()
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()