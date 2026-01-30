/**
 * AquaGuard 韩家家庭智能系统 - ESP8266 单色灯兼容版
 *
 * 适用硬件：单色 LED (如红色 LED 模块)
 * 功能：
 * - 适配 AquaGuard 桌面软件协议 (API 兼容)
 * - 支持 开/关
 * - 支持 亮度调节 (通过颜色亮度映射)
 *
 * 接线：
 * - LED 正极 -> D2 (GPIO 4) 或自定义引脚
 * - LED 负极 -> GND
 */

#include <ESP8266WebServer.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h> // MQTT Support

// ============ Wi-Fi 配置 ============
const char *ssid = "中国电信";     // 请修改为您的 Wi-Fi 名称
const char *password = "12345678"; // 请修改为您的 Wi-Fi 密码

// ============ Bemfa MQTT 配置 ============
const char *mqtt_server = "bemfa.com";
const int mqtt_port = 9501;
const char *bemfa_uid = "33754230b4834bf1b224873383afbe10"; // 用户私钥
const char *bemfa_topic = "ciyilhknB002";                   // 控制主题

WiFiClient espClient;
PubSubClient client(espClient);

// ============ 硬件配置 ============
#define LED_PIN D2 // LED 连接的引脚 (GPIO 4)
// 注意：如果是板载 LED (D4/GPIO2)，通常是低电平点亮，逻辑需反转

// ============ 全局变量 ============
ESP8266WebServer server(80);

// 当前状态
bool powerState = false;         // 开关状态
uint8_t currentBrightness = 255; // 当前亮度 (0-255)
// 虚拟颜色 (为了欺骗上位机显示正确的颜色)
uint8_t currentR = 255;
uint8_t currentG = 0;
uint8_t currentB = 0;
String currentMode = "static";

// ============ 函数声明 ============
void handleRoot();
void handlePower();
void handleColor();
void handleMode();
void handleStatus();
void handleNotFound();
void updateLED();
void handlePowerArg(String state); // Forward declaration
void callback(char *topic, byte *payload, unsigned int length);
void reconnect();

// ============ 初始化 ============
void setup() {
  Serial.begin(115200);
  Serial.println("\n\n=== AquaGuard 单色灯兼容版 ===");

  // 初始化引脚
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW); // 默认关闭

  // 连接 Wi-Fi
  Serial.print("连接 Wi-Fi: ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    // 连接时慢闪
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWi-Fi 连接成功！");
    Serial.print("IP 地址: ");
    Serial.println(WiFi.localIP());

    // 成功快闪 3 下
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      digitalWrite(LED_PIN, LOW);
      delay(100);
    }
  } else {
    Serial.println("\nWi-Fi 连接失败！");
  }

  // 配置路由 (完全兼容 AquaGuard API)
  server.on("/", handleRoot);
  server.on("/power", handlePower); // 同时也兼容旧的 /on /off 逻辑
  server.on("/on", []() { handlePowerArg("on"); });
  server.on("/off", []() { handlePowerArg("off"); });
  server.on("/color", handleColor);
  server.on("/mode", handleMode);
  server.on("/status", handleStatus);
  server.onNotFound(handleNotFound);

  server.begin();
  Serial.println("HTTP 服务器已启动");

  // MQTT 初始化
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

// ============ 主循环 ============
void loop() {
  server.handleClient();

  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

// ============ LED 控制逻辑 ============
void updateLED() {
  if (!powerState) {
    analogWrite(LED_PIN, 0); // 关闭
    return;
  }

  if (currentMode == "breath") {
    // 简单的呼吸效果模拟
    int val = (exp(sin(millis() / 2000.0 * PI)) - 0.36787944) * 108.0;
    // 缩放到当前亮度
    val = map(val, 0, 255, 0, currentBrightness);
    analogWrite(LED_PIN, val * 4); // ESP8266 PWM 是 0-1023
  } else {
    // 静态亮度
    // 映射 0-255 到 0-1023
    int pwmValue = map(currentBrightness, 0, 255, 0, 1023);
    analogWrite(LED_PIN, pwmValue);
  }
}

// ============ API 处理 ============

void handleRoot() {
  String html = "<h1>AquaGuard Simple LED</h1>";
  html += "<p>Status: " + String(powerState ? "ON" : "OFF") + "</p>";
  html += "<p>Brightness: " + String(currentBrightness) + "</p>";
  html += "<p><a href='/on'>ON</a> | <a href='/off'>OFF</a></p>";
  server.send(200, "text/html", html);
}

void handlePowerArg(String state) {
  if (state == "on") {
    powerState = true;
    analogWrite(LED_PIN, map(currentBrightness, 0, 255, 0, 1023));
  } else {
    powerState = false;
    analogWrite(LED_PIN, 0);
  }
  server.send(200, "application/json",
              "{\"success\":true,\"power\":\"" + state + "\"}");
}

void handlePower() {
  if (server.hasArg("state")) {
    handlePowerArg(server.arg("state"));
  } else {
    server.send(400, "text/plain", "Missing state");
  }
}

void handleColor() {
  if (server.hasArg("r") && server.hasArg("g") && server.hasArg("b")) {
    currentR = server.arg("r").toInt();
    currentG = server.arg("g").toInt();
    currentB = server.arg("b").toInt();

    // 计算亮度 (简单的平均值)
    currentBrightness = (currentR + currentG + currentB) / 3;

    // 实时更新
    if (powerState) {
      analogWrite(LED_PIN, map(currentBrightness, 0, 255, 0, 1023));
    }

    String response = "{\"success\":true,\"color\":{\"r\":" + String(currentR) +
                      ",\"g\":" + String(currentG) +
                      ",\"b\":" + String(currentB) + "}}";
    server.send(200, "application/json", response);
  } else {
    server.send(400, "text/plain", "Missing RGB");
  }
}

void handleMode() {
  if (server.hasArg("type")) {
    currentMode = server.arg("type");
    server.send(200, "application/json",
                "{\"success\":true,\"mode\":\"" + currentMode + "\"}");
  }
}

void handleStatus() {
  // 关键：构建符合 Desktop App 预期的 JSON 格式
  String response = "{";
  response += "\"power\":\"" + String(powerState ? "on" : "off") + "\",";
  response += "\"mode\":\"" + currentMode + "\",";
  response += "\"color\":{\"r\":" + String(currentR);
  response += ",\"g\":" + String(currentG);
  response += ",\"b\":" + String(currentB) + "},";
  response += "\"wifi_signal\":" + String(WiFi.RSSI());
  response += "}";
  server.send(200, "application/json", response);
}

void handleNotFound() { server.send(404, "text/plain", "Not Found"); }

// ============ MQTT 辅助函数 ============

void callback(char *topic, byte *payload, unsigned int length) {
  String msg = "";
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  Serial.print("收到 MQTT 消息 [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(msg);

  // 巴法云默认发送 "on" 或 "off"
  if (msg == "on") {
    handlePowerArg("on");
  } else if (msg == "off") {
    handlePowerArg("off");
  }
  // 如果需要亮度控制，可以解析 "on#50" 之类的格式，这里暂只处理开关
}

void reconnect() {
  // 如果已经连接则通过
  if (client.connected())
    return;

  Serial.print("尝试连接 MQTT...");
  // 尝试连接 (使用 UID 作为 Client ID)
  if (client.connect(bemfa_uid)) {
    Serial.println("已连接");
    // 订阅主题
    client.subscribe(bemfa_topic);
  } else {
    Serial.print("失败, rc=");
    Serial.print(client.state());
    Serial.println(" 稍后重试");
    // 不要在 loop 中使用长 delay，会阻塞 HTTP Server
    // 这里简单处理，生产环境建议使用非阻塞计时器
  }
}
