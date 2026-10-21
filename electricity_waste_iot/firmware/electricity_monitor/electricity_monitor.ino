/*
 * IoT-Based Intelligent Electricity Waste Detection
 * ESP32 Firmware (Arduino IDE)
 *
 * Hardware:
 *   - ESP32 DevKit
 *   - ACS712 / SCT-013 current sensor  (pin 34)
 *   - PIR motion sensor HC-SR501       (pin 27)
 *   - Optional: Relay module           (pin 26)
 *
 * SAFETY: Use properly rated, isolated sensors.
 *         Prefer low-voltage / CT-based sensing for student demos.
 *         Qualified supervision required when working with mains.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ---------- CONFIG ----------
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* SERVER_URL    = "http://192.168.1.100:5000/api/ingest";  // change to PC IP

const int PIN_CURRENT = 34;   // ADC for current sensor
const int PIN_PIR     = 27;   // digital PIR
const int PIN_RELAY   = 26;   // optional relay (active LOW or HIGH depending on module)

const float VOLTAGE       = 230.0;   // mains voltage (India)
const float ACS_SENSITIVITY = 0.185; // V/A for ACS712 5A variant (adjust for your sensor)
const float ADC_VREF      = 3.3;
const int   ADC_MAX       = 4095;

const unsigned long SAMPLE_INTERVAL_MS = 10000;  // send every 10 s
const float WASTE_POWER_W = 40.0;                // local threshold

// ---------- STATE ----------
unsigned long lastSend = 0;
bool relayOn = false;

float readCurrentAmps() {
  // Average several ADC samples for stability
  long sum = 0;
  const int N = 50;
  for (int i = 0; i < N; i++) {
    sum += analogRead(PIN_CURRENT);
    delay(2);
  }
  float voltage = (sum / (float)N) * (ADC_VREF / ADC_MAX);
  // ACS712 mid-point is ~1.65 V at 0 A (for 3.3 V supply with divider or 5 V sensor)
  float zeroPoint = ADC_VREF / 2.0;
  float amps = (voltage - zeroPoint) / ACS_SENSITIVITY;
  return abs(amps);
}

int readOccupancy() {
  return digitalRead(PIN_PIR) == HIGH ? 1 : 0;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_RELAY, OUTPUT);
  digitalWrite(PIN_RELAY, HIGH);  // relay off (adjust polarity)

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (millis() - lastSend < SAMPLE_INTERVAL_MS) return;
  lastSend = millis();

  float currentA = readCurrentAmps();
  float powerW   = currentA * VOLTAGE;
  int   occ      = readOccupancy();

  Serial.printf("I=%.3f A  P=%.1f W  Occupancy=%d\n", currentA, powerW, occ);

  // Optional local relay control: cut power if waste detected
  if (occ == 0 && powerW >= WASTE_POWER_W) {
    // Uncomment only after confirming safe load control
    // digitalWrite(PIN_RELAY, LOW);  // turn relay ON (cut load)
    // relayOn = true;
  } else if (relayOn && occ == 1) {
    // digitalWrite(PIN_RELAY, HIGH);
    // relayOn = false;
  }

  // Send to dashboard
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<200> doc;
    doc["current_a"]  = currentA;
    doc["power_w"]    = powerW;
    doc["occupancy"]  = occ;
    doc["voltage_v"]  = VOLTAGE;

    String body;
    serializeJson(doc, body);
    int code = http.POST(body);
    Serial.printf("POST %d\n", code);
    http.end();
  } else {
    Serial.println("WiFi disconnected, reconnecting...");
    WiFi.reconnect();
  }
}
