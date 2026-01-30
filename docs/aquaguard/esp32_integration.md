这是一个为你整理好的标准技术文档。你可以直接将其保存为 `AquaGuard_Node_Integration.md`，用于指导系统集成开发。

------

# AquaGuard 鱼缸管理系统 - 硬件节点集成文档 (ESP32)

**文档版本:** v1.0.0

**硬件平台:** 乐鑫 ESP32-WROOM-32E + GPIO 拓展板

**适用模块:**

1. **水温:** DS18B20 防水探头
2. **水位:** XKC-Y25-V 非接触式传感器
3. **灯光:** 普通单色 LED 模块 (修改版接法)

------

## 1. 硬件接线规范 (Hardware Configuration)

### 1.1 拓展板跳线设置 (关键)

- **位置:** 拓展板右下角黄色跳线帽 (Jump Interface)
- **设置:** 必须插在 **5V** 侧 (连接中间针脚与 5V 针脚)
- **目的:** 确保水位传感器获得足够的穿透电压。

### 1.2 模块接线表 (Pinout)

| **模块名称**   | **模块引脚线色** | **接入拓展板位置**     | **备注/警告**                                 |
| -------------- | ---------------- | ---------------------- | --------------------------------------------- |
| **水位传感器** | **棕色 (VCC)**   | **D16 - V** (中间红色) | 5V 供电                                       |
| (XKC-Y25-V)    | **蓝色 (GND)**   | **D16 - G** (下方黑色) | 共地                                          |
|                | **黄色 (OUT)**   | **D16 - S** (上方黄色) | 信号输入                                      |
|                | **黑色 (MODE)**  | **悬空**               | **不接** (使用绝缘胶带包裹)                   |
|                |                  |                        |                                               |
| **温度传感器** | **红色 (VCC)**   | **3.3V 独立排针**      | **⚠️ 禁止接中间红排 (5V)**，否则可能损坏 ESP32 |
| (DS18B20)      | **黑色 (GND)**   | **GND**                | 任意 G 接口                                   |
|                | **黄色 (DAT)**   | **D4 - S** (上方黄色)  | 信号输入 (GPIO 4)                             |
|                |                  |                        |                                               |
| **LED 灯模块** | **VCC (+)**      | **D5 - S** (上方黄色)  | **⚠️ 特殊接法:** 利用 GPIO 供电控制开关        |
| (普通单色)     | **GND (-)**      | **D5 - G** (下方黑色)  | 共地                                          |
|                | **DAT/IN**       | **悬空**               | 该模块此引脚无效，不接                        |

------

## 2. 软件配置 (Software Setup)

### 2.1 开发环境

- **IDE:** Arduino IDE 2.x
- **开发板选择:** `ESP32 Dev Module`
- **依赖库 (Library Manager 安装):**
  1. `PubSubClient` (by Nick O'Leary) - MQTT支持
  2. `OneWire` (by Paul Stoffregen) - 单总线支持
  3. `DallasTemperature` (by Miles Burton) - 温度传感器支持

### 2.2 固件源码 (Firmware)

C++

```
/**
 * AquaGuard Node Firmware v1.0
 * 功能: 采集水温、水位，控制灯光，提供 HTTP/MQTT 接口
 */

#include <WiFi.h>
#include <WebServer.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ================= 配置区域 (需修改) =================
const char *ssid = "你的WiFi名称";
const char *password = "你的WiFi密码";

// MQTT (巴法云 Bemfa)
const char *mqtt_server = "bemfa.com";
const int mqtt_port = 9501;
const char *bemfa_uid = "33754230b4834bf1b224873383afbe10"; // 私钥
const char *bemfa_topic = "ciyilhknB002"; // 主题

// ================= 引脚定义 =================
#define LED_PIN     5   // 灯光 (连接到 S 脚供电)
#define TEMP_PIN    4   // 温度 (DS18B20)
#define WATER_PIN   16  // 水位 (XKC-Y25-V)

// ================= 全局对象 =================
WebServer server(80);
WiFiClient espClient;
PubSubClient client(espClient);
OneWire oneWire(TEMP_PIN);
DallasTemperature sensors(&oneWire);

// 状态变量
bool lightState = false;
float currentTemp = 0.0;
int waterLevel = 0; // 1=正常(有水), 0=缺水
unsigned long lastSensorRead = 0;

// ================= 函数声明 =================
void controlLight(bool on);
void handleStatus();
void callback(char *topic, byte *payload, unsigned int length);
void reconnect();

void setup() {
  Serial.begin(115200);
  
  // 硬件初始化
  pinMode(LED_PIN, OUTPUT);
  pinMode(WATER_PIN, INPUT);
  digitalWrite(LED_PIN, LOW); // 默认关灯
  sensors.begin();

  // WiFi 连接
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  
  // HTTP 路由配置
  server.on("/status", handleStatus); // 上位机获取数据接口
  
  server.on("/on", []() { 
    controlLight(true); 
    server.send(200, "application/json", "{\"success\":true,\"state\":\"on\"}");
  });
  
  server.on("/off", []() { 
    controlLight(false); 
    server.send(200, "application/json", "{\"success\":true,\"state\":\"off\"}");
  });

  server.begin();

  // MQTT 初始化
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  server.handleClient();
  if (!client.connected()) reconnect();
  client.loop();

  // 传感器轮询 (2秒间隔)
  if (millis() - lastSensorRead > 2000) {
    lastSensorRead = millis();
    
    // 读取温度
    sensors.requestTemperatures();
    float t = sensors.getTempCByIndex(0);
    if (t > -100) currentTemp = t;

    // 读取水位 (黑色线悬空: 有水=HIGH, 无水=LOW)
    waterLevel = digitalRead(WATER_PIN);
  }
}

// 业务逻辑: 灯光控制
void controlLight(bool on) {
  lightState = on;
  digitalWrite(LED_PIN, on ? HIGH : LOW);
}

// 接口: JSON 状态返回
void handleStatus() {
  String json = "{";
  json += "\"power\":\"" + String(lightState ? "on" : "off") + "\",";
  json += "\"temperature\":" + String(currentTemp, 1) + ",";
  json += "\"water_level\":" + String(waterLevel) + ",";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\"";
  json += "}";
  server.send(200, "application/json", json);
}

// MQTT 回调
void callback(char *topic, byte *payload, unsigned int length) {
  String msg = "";
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
  if (msg == "on") controlLight(true);
  else if (msg == "off") controlLight(false);
}

// MQTT 重连
void reconnect() {
  if (client.connect(bemfa_uid)) {
    client.subscribe(bemfa_topic);
  }
}
```

------

## 3. 接口文档 (API Integration)

上位机系统可通过 HTTP 或 MQTT 与该硬件节点通信。

### 3.1 状态查询接口 (轮询)

系统应每隔 3-5 秒调用一次此接口以更新 UI。

- **URL:** `http://[ESP32_IP]/status`
- **Method:** `GET`
- **Response (JSON):**

JSON

```
{
  "power": "on",          // 灯光状态: "on" 或 "off"
  "temperature": 25.4,    // 实时水温 (摄氏度)
  "water_level": 1,       // 水位状态: 1=正常(满), 0=缺水(需报警)
  "ip": "192.168.31.161"  // 设备当前 IP
}
```

### 3.2 控制接口 (HTTP)

- **开灯:** `GET http://[ESP32_IP]/on`
- **关灯:** `GET http://[ESP32_IP]/off`

### 3.3 控制接口 (MQTT / 巴法云)

- **Broker:** `bemfa.com` (Port: 9501)
- **Topic:** `ciyilhknB002`
- **Payload:**
  - 发送 `on` -> 开启设备
  - 发送 `off` -> 关闭设备

------

## 4. 异常排查 (Troubleshooting)

1. **水温显示 -127 或 85:**
   - 检查 DS18B20 是否接到了 3.3V (不要接 5V)。
   - 检查 DS18B20 适配器是否自带电阻 (通常带)。
2. **灯无法控制 (常亮或不亮):**
   - 确认 **VCC 线** 是否插在了拓展板的 **S (最上排)** 针脚。
   - 确认 **中间的 V (红色排针)** 没有任何连接。
3. **水位检测反向:**
   - 确认传感器黑色线(Mode)必须**悬空**。
   - 确认代码逻辑为 `HIGH = 有水`。