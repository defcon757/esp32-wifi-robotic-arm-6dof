from flask import Flask, render_template, request, jsonify
from arm_controller import RobotArm
from config import ARM_IP, CAMERA_IP

app = Flask(__name__)

arm = RobotArm()

print("===================================")
print("🚀 ROBOT ARM FLASK SERVER STARTED")
print("===================================")


@app.route("/")
def index():
    print("🌐 GUI LOADED (GET /)")
    return render_template("index.html", camera_ip=CAMERA_IP)


@app.route("/servo", methods=["POST"])
def servo():
    data = request.json
    print("\n================ SERVO ================")
    print("📥 DATA:", data)
    arm.move_servo(data["name"], data["delta"])
    return jsonify(success=True)


@app.route("/servo_set", methods=["POST"])
def servo_set():
    data = request.json
    print("\n================ SERVO SET ================")
    print("📥 DATA:", data)
    arm.set_servo(data["name"], data["angle"])
    return jsonify(success=True)


@app.route("/motor_nudge", methods=["POST"])
def motor_nudge():
    data = request.json
    print("\n================ MOTOR NUDGE ================")
    print("📥 DATA:", data)
    arm.nudge_motor(data["name"], data["delta"])
    return jsonify(success=True)


@app.route("/motor_stop", methods=["POST"])
def motor_stop():
    data = request.json
    print("\n================ MOTOR STOP ================")
    print("📥 DATA:", data)
    arm.stop_motor(data["name"])
    return jsonify(success=True)


@app.route("/home", methods=["POST"])
def home():
    print("\n================ HOME ================")
    arm.home()
    return jsonify(success=True)


@app.route("/stop", methods=["POST"])
def stop():
    print("\n================ EMERGENCY STOP ================")
    arm.stop_all_motors()
    return jsonify(success=True)

@app.route("/status")
def status():

    return jsonify({
        "servo_angles": arm.servo_angles,
        "motor_pulse": arm.motor_pulse,
        "motor_speed": arm.motor_speed
    })


if __name__ == "__main__":
    print("🔌 Connecting Flask to robot system...")
    app.run(host="0.0.0.0", port=5000, debug=True)