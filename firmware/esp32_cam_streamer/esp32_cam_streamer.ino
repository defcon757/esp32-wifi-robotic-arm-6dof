#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// =========================
// WIFI — update before flashing
// =========================
const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// =========================
// AI THINKER ESP32-CAM PIN DEFINITIONS
// Do not change unless using a different ESP32-CAM module.
// =========================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5

#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

WebServer server(80);

// =========================
// /stream — MJPEG stream handler
// Sends a multipart/x-mixed-replace HTTP response with
// JPEG frames captured continuously from the OV2640 sensor.
// The Python GUI embeds this URL in an <img> tag for live display.
// =========================
void handle_jpg_stream(void) {

  WiFiClient client = server.client();

  // Send HTTP header for multipart stream
  String response =
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
  server.sendContent(response);

  Serial.println("Stream started");

  while (client.connected()) {

    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      continue;
    }

    // Send frame boundary + JPEG headers
    response  = "--frame\r\n";
    response += "Content-Type: image/jpeg\r\n";
    response += "Content-Length: " + String(fb->len) + "\r\n\r\n";
    server.sendContent(response);

    // Send raw JPEG bytes
    client.write(fb->buf, fb->len);
    server.sendContent("\r\n");

    esp_camera_fb_return(fb);

    // ~10 FPS at 100 ms delay — increase delay to reduce bandwidth
    delay(100);
  }

  Serial.println("Stream ended (client disconnected)");
}

// =========================
// / — simple root page for browser testing
// =========================
void handle_root() {
  String html =
    "<html>"
    "<body style='margin:0;background:black;'>"
    "<img src='/stream' width='100%'>"
    "</body>"
    "</html>";
  server.send(200, "text/html", html);
}

// =========================
// SETUP
// =========================
void setup() {

  Serial.begin(115200);
  Serial.println("\nESP32-CAM starting...");

  // ---- Camera configuration ----
  camera_config_t config;

  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;

  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;

  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;

  config.xclk_freq_hz = 10000000;     // 10 MHz XCLK
  config.pixel_format = PIXFORMAT_JPEG;

  // Low resolution + low quality = lower latency over Wi-Fi
  // Increase FRAMESIZE to FRAMESIZE_VGA (640×480) for better image
  // at the cost of higher latency / bandwidth.
  config.frame_size   = FRAMESIZE_QQVGA; // 160×120
  config.jpeg_quality = 20;              // 0 = best, 63 = worst
  config.fb_count     = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    while (true) delay(1000); // halt
  }
  Serial.println("Camera OK");

  // ---- Wi-Fi ----
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected — stream at: http://");
  Serial.print(WiFi.localIP());
  Serial.println("/stream");

  // ---- Routes ----
  server.on("/",       HTTP_GET, handle_root);
  server.on("/stream", HTTP_GET, handle_jpg_stream);
  server.begin();
  Serial.println("HTTP server started");
}

// =========================
// LOOP — only handles HTTP clients
// =========================
void loop() {
  server.handleClient();
  delay(1);
}
