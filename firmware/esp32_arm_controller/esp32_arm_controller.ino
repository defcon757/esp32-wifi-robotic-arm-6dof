#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <ArduinoJson.h>

// =========================
// WIFI — update before flashing
// =========================
const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

WebServer server(80);
Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver();

// =========================
// REV SRS PULSE VALUES (50Hz)
// 102 = full reverse, 307 = STOP, 512 = full forward
// =========================
#define SERVO_MIN  102
#define SERVO_MAX  512
#define CONT_STOP  307
#define DEAD_BAND  5

// =========================
// PCA9685 CHANNEL MAP
// =========================
#define BASE           0
#define LEFT_SHOULDER  1
#define RIGHT_SHOULDER 2
#define ELBOW          3
#define WRIST_UD       4
#define WRIST_ROT      5
#define CLAW           6

// =========================
// STATE
// motorPulse: direct PWM pulse value, 307 = stop
// servoAngle: 0-270° positional
// =========================
int motorPulse[2] = {CONT_STOP, CONT_STOP}; // [0]=base, [1]=shoulder
int servoAngle[4] = {135, 135, 135, 135};   // elbow, wrist_ud, wrist_rotate, claw

// =========================
// CHANGE DETECTION — avoids re-writing unchanged channels
// =========================
int lastPulse[16];

// =========================
// PWM HELPERS
// =========================

// Maps a 0–270° angle to the PCA9685 pulse range
int angleToPulse(int angle) {
  return map(constrain(angle, 0, 270), 0, 270, SERVO_MIN, SERVO_MAX);
}

// Only writes to PCA9685 if the value has changed
void setServoIfChanged(int ch, int pulse) {
  pulse = constrain(pulse, SERVO_MIN, SERVO_MAX);
  if (pulse != lastPulse[ch]) {
    pca.setPWM(ch, 0, pulse);
    lastPulse[ch] = pulse;
  }
}

// Unconditional write (used for home/init)
void setServoDirect(int ch, int pulse) {
  pca.setPWM(ch, 0, pulse);
  lastPulse[ch] = pulse;
}

// =========================
// TARGETED JOINT UPDATERS
// Python increments pulses; ESP32 just writes what it receives.
// Shoulder mirrors LEFT and RIGHT around CONT_STOP so both
// motors push in the same physical direction.
// =========================

void updateBase() {
  int pulse = motorPulse[0];
  if (abs(pulse - CONT_STOP) < DEAD_BAND) pulse = CONT_STOP;
  setServoIfChanged(BASE, pulse);
}

void updateShoulder() {
  int pulse    = motorPulse[1];
  if (abs(pulse - CONT_STOP) < DEAD_BAND) pulse = CONT_STOP;
  int mirrored = CONT_STOP + (CONT_STOP - pulse);
  setServoIfChanged(LEFT_SHOULDER,  pulse);
  setServoIfChanged(RIGHT_SHOULDER, mirrored);
}

void updateElbow()    { setServoIfChanged(ELBOW,    angleToPulse(servoAngle[0])); }
void updateWristUD()  { setServoIfChanged(WRIST_UD, angleToPulse(servoAngle[1])); }
void updateWristRot() { setServoIfChanged(WRIST_ROT, angleToPulse(servoAngle[2])); }
void updateClaw()     { setServoIfChanged(CLAW,     angleToPulse(servoAngle[3])); }

// =========================
// /update  POST handler
// Receives a JSON payload from the Flask server and updates
// only the joints listed in the "active" array.
// =========================
void handleUpdate() {

  Serial.println("\n[UPDATE]");

  String body = server.arg("plain");
  Serial.println(body);

  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, body);

  if (error) {
    Serial.println("JSON parse failed");
    server.send(400, "text/plain", "Bad JSON");
    return;
  }

  // Read motor pulses — Python drives the increments
  motorPulse[0] = doc["motor_pulse"]["base"]     | motorPulse[0];
  motorPulse[1] = doc["motor_pulse"]["shoulder"] | motorPulse[1];

  // Positional servos fall back to current angle if not in payload
  servoAngle[0] = doc["servo_angles"]["elbow"]        | servoAngle[0];
  servoAngle[1] = doc["servo_angles"]["wrist_ud"]     | servoAngle[1];
  servoAngle[2] = doc["servo_angles"]["wrist_rotate"] | servoAngle[2];
  servoAngle[3] = doc["servo_angles"]["claw"]         | servoAngle[3];

  // Only update joints listed as active
  JsonArray active = doc["active"].as<JsonArray>();
  for (JsonVariant v : active) {
    String joint = v.as<String>();
    Serial.print("  Updating: "); Serial.println(joint);
    if      (joint == "base")         updateBase();
    else if (joint == "shoulder")     updateShoulder();
    else if (joint == "elbow")        updateElbow();
    else if (joint == "wrist_ud")     updateWristUD();
    else if (joint == "wrist_rotate") updateWristRot();
    else if (joint == "claw")         updateClaw();
  }

  server.send(200, "text/plain", "OK");
}

// =========================
// /home  POST handler
// Centers all joints unconditionally.
// =========================
void handleHome() {

  Serial.println("\n[HOME]");

  motorPulse[0] = CONT_STOP;
  motorPulse[1] = CONT_STOP;
  servoAngle[0] = servoAngle[1] = servoAngle[2] = servoAngle[3] = 135;

  setServoDirect(BASE,           CONT_STOP);
  setServoDirect(LEFT_SHOULDER,  CONT_STOP);
  setServoDirect(RIGHT_SHOULDER, CONT_STOP);
  setServoDirect(ELBOW,          angleToPulse(135));
  setServoDirect(WRIST_UD,       angleToPulse(135));
  setServoDirect(WRIST_ROT,      angleToPulse(135));
  setServoDirect(CLAW,           angleToPulse(135));

  server.send(200, "text/plain", "HOME OK");
}

// =========================
// SETUP
// =========================
void setup() {

  Serial.begin(115200);
  Serial.println("\nBooting ESP32 Arm Controller...");

  for (int i = 0; i < 16; i++) lastPulse[i] = -1;

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // Init PCA9685 at 50 Hz (standard servo frequency)
  pca.begin();
  pca.setPWMFreq(50);

  // Send all joints to home position on boot
  setServoDirect(BASE,           CONT_STOP);
  setServoDirect(LEFT_SHOULDER,  CONT_STOP);
  setServoDirect(RIGHT_SHOULDER, CONT_STOP);
  setServoDirect(ELBOW,          angleToPulse(135));
  setServoDirect(WRIST_UD,       angleToPulse(135));
  setServoDirect(WRIST_ROT,      angleToPulse(135));
  setServoDirect(CLAW,           angleToPulse(135));

  // Register HTTP routes
  server.on("/update", HTTP_POST, handleUpdate);
  server.on("/home",   HTTP_POST, handleHome);

  server.begin();
  Serial.println("HTTP server started");
}

// =========================
// LOOP
// Arm controller is purely reactive — all motion is commanded
// by the Python server. The loop only services incoming HTTP requests.
// =========================
void loop() {
  server.handleClient();
}
