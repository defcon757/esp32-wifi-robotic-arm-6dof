console.log("🚀 Robot Arm JS Loaded");

const DEBUG = true;
function log(...args) { if (DEBUG) console.log(...args); }

// =========================
// HOLD SYSTEM
// =========================
let holdInterval = null;

function startHold(action, onRelease) {
  stopHold();
  action();
  holdInterval = setInterval(action, 100);
  holdInterval._onRelease = onRelease;
}

function stopHold() {
  if (holdInterval) {
    clearInterval(holdInterval);
    if (holdInterval._onRelease) holdInterval._onRelease();
    holdInterval = null;
  }
}

document.addEventListener("contextmenu", e => e.preventDefault());


// =========================
// MOTOR NUDGE (CONTINUOUS)
// Each interval nudges the pulse by a fixed delta and holds there.
// On release, motor_stop resets pulse to CONT_STOP (307).
// delta tuning: larger = faster per tick, smaller = finer control
// =========================
async function motorNudge(name, delta) {
  log("⚙ Motor nudge:", name, "Δ", delta);
  try {
    const res = await fetch("/motor_nudge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, delta })
    });
    log("✅ Nudge:", await res.json());
  } catch (e) {
    console.error("❌ Motor nudge failed:", e);
  }
}

async function motorStop(name) {
  log("🛑 Motor stop:", name);
  try {
    const res = await fetch("/motor_stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name })
    });
    log("✅ Motor stop:", await res.json());
  } catch (e) {
    console.error("❌ Motor stop failed:", e);
  }
}

function startMotor(name, delta) {
  startHold(
    () => motorNudge(name, delta),
    () => motorStop(name)
  );
}


// =========================
// SERVO CONTROL (RELATIVE)
// =========================
async function moveServo(name, delta) {
  log("🎮 Servo:", name, "Δ", delta);
  try {
    const res = await fetch("/servo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, delta })
    });
    log("✅ Servo:", await res.json());
  } catch (e) {
    console.error("❌ Servo failed:", e);
  }
}

function startServo(name, delta) {
  startHold(
    () => moveServo(name, delta),
    null
  );
}


// =========================
// SERVO SET (ABSOLUTE)
// =========================
async function setServo(name, angle) {
  log("📐 Set servo:", name, "→", angle);
  try {
    const res = await fetch("/servo_set", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, angle })
    });
    log("✅ Set servo:", await res.json());
  } catch (e) {
    console.error("❌ Set servo failed:", e);
  }
}


// =========================
// EMERGENCY STOP
// =========================
async function stopAll() {
  stopHold();
  log("🛑 EMERGENCY STOP");
  try {
    const res = await fetch("/stop", { method: "POST" });
    log("🛑 Stop:", await res.json());
  } catch (e) {
    console.error("❌ Stop failed:", e);
  }
}


// =========================
// HOME
// =========================
async function homeArm() {
  stopHold();
  log("🏠 HOME");
  try {
    const res = await fetch("/home", { method: "POST" });
    log("🏠 Home:", await res.json());
  } catch (e) {
    console.error("❌ Home failed:", e);
  }
}

// =========================
// LIVE ARM STATUS
// =========================

async function updateArmStatus() {

  try {

    const response = await fetch("/status");

    const data = await response.json();

    // -------------------------
    // Servo Angles
    // -------------------------

    const elbowAngle = data.servo_angles.elbow;
    const wristUdAngle = data.servo_angles.wrist_ud;
    const wristRotateAngle = data.servo_angles.wrist_rotate;
    const clawAngle = data.servo_angles.claw;

    const basePulse = data.motor_pulse.base;
    const shoulderPulse = data.motor_pulse.shoulder;

    // -------------------------
    // Update Text Values
    // -------------------------

    const elbowText = document.getElementById("elbow-angle");
    const wristUdText = document.getElementById("wristud-angle");
    const wristRotateText = document.getElementById("wristrotate-angle");
    const clawText = document.getElementById("claw-angle");

    const baseText = document.getElementById("base-pulse");
    const shoulderText = document.getElementById("shoulder-pulse");

    if (elbowText) elbowText.textContent = `${elbowAngle}°`;
    if (wristUdText) wristUdText.textContent = `${wristUdAngle}°`;
    if (wristRotateText) wristRotateText.textContent = `${wristRotateAngle}°`;
    if (clawText) clawText.textContent = `${clawAngle}°`;

    if (baseText) baseText.textContent = basePulse;
    if (shoulderText) shoulderText.textContent = shoulderPulse;

    // -------------------------
    // Update Progress Bars
    // -------------------------

    const elbowBar = document.getElementById("elbow-bar");
    const wristUdBar = document.getElementById("wristud-bar");
    const wristRotateBar = document.getElementById("wristrotate-bar");
    const clawBar = document.getElementById("claw-bar");

    if (elbowBar)
      elbowBar.style.width = `${(elbowAngle / 270) * 100}%`;

    if (wristUdBar)
      wristUdBar.style.width = `${(wristUdAngle / 270) * 100}%`;

    if (wristRotateBar)
      wristRotateBar.style.width = `${(wristRotateAngle / 270) * 100}%`;

    if (clawBar)
      clawBar.style.width = `${(clawAngle / 270) * 100}%`;

  } catch (e) {

    console.error("❌ Status update failed:", e);

  }
}


// =========================
// START STATUS POLLING
// =========================

setInterval(updateArmStatus, 250);

window.addEventListener("load", () => {
  updateArmStatus();
});