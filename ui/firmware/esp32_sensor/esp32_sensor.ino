/**
 * AquaGuard 韩家家庭智能系统 - ESP32 环境感知节点
 * 
 * 功能：
 * - 采集水温（DS18B20）
 * - 采集水质 TDS 值
 * - 监测水位状态
 * - 提供 RESTful API 接口
 * 
 * 接口：
 * - GET /status    获取所有传感器数据
 */

#include <WiFi.h>
#include <WebServer.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ============ Wi-Fi 配置 ============
const char* ssid = "YOUR_WIFI_SSID";      // 修改为您的 Wi-Fi 名称
const char* password = "YOUR_WIFI_PASSWORD"; // 修改为您的 Wi-Fi 密码

// ============ 引脚配置 ============
#define TEMP_PIN      25    // DS18B20 水温传感器
#define TDS_PIN       34    // TDS 水质传感器 (ADC1)
#define WATER_LEVEL_PIN 26  // XKC-Y25-V 水位传感器

// ============ TDS 配置 ============
#define VREF 3.3            // ADC 参考电压
#define TDS_FACTOR 0.5      // TDS 转换系数

// ============ 全局变量 ============
OneWire oneWire(TEMP_PIN);
DallasTemperature tempSensor(&oneWire);
WebServer server(80);

// 系统运行时间
unsigned long startTime = 0;

// 传感器数据
float currentTemperature = 0.0;
int currentTDS = 0;
int waterLevel = 1;  // 1: 正常, 0: 缺水
bool alertFlag = false;

// 数据采集计时器
unsigned long lastTempRead = 0;
unsigned long lastTDSRead = 0;

// TDS 滤波缓冲区
#define TDS_SAMPLES 10
int tdsBuffer[TDS_SAMPLES];
int tdsBufferIndex = 0;

// ============ 函数声明 ============
void handleRoot();
void handleStatus();
void handleNotFound();
void readTemperature();
void readTDS();
void readWaterLevel();
int getMedianTDS();

// ============ 初始化 ============
void setup() {
    Serial.begin(115200);
    Serial.println("\n\n=== AquaGuard ESP32 环境感知节点 ===");
    
    // 初始化引脚
    pinMode(WATER_LEVEL_PIN, INPUT);
    
    // 初始化温度传感器
    tempSensor.begin();
    tempSensor.setResolution(12);  // 12位精度
    
    // 初始化 TDS 缓冲区
    for (int i = 0; i < TDS_SAMPLES; i++) {
        tdsBuffer[i] = 0;
    }
    
    // 连接 Wi-Fi
    Serial.print("连接 Wi-Fi: ");
    Serial.println(ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWi-Fi 连接成功！");
        Serial.print("IP 地址: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\nWi-Fi 连接失败！");
    }
    
    // 配置 HTTP 服务器路由
    server.on("/", handleRoot);
    server.on("/status", handleStatus);
    server.onNotFound(handleNotFound);
    
    // 启动服务器
    server.begin();
    Serial.println("HTTP 服务器已启动");
    
    // 记录启动时间
    startTime = millis();
    
    // 首次读取传感器
    readTemperature();
    readTDS();
    readWaterLevel();
}

// ============ 主循环 ============
void loop() {
    server.handleClient();
    
    unsigned long currentTime = millis();
    
    // 每 2 秒读取温度
    if (currentTime - lastTempRead >= 2000) {
        lastTempRead = currentTime;
        readTemperature();
    }
    
    // 每 5 秒读取 TDS
    if (currentTime - lastTDSRead >= 5000) {
        lastTDSRead = currentTime;
        readTDS();
    }
    
    // 实时读取水位
    readWaterLevel();
    
    // 检查报警条件
    checkAlertConditions();
}

// ============ 传感器读取 ============
void readTemperature() {
    tempSensor.requestTemperatures();
    float temp = tempSensor.getTempCByIndex(0);
    
    // 有效性检查
    if (temp != DEVICE_DISCONNECTED_C && temp > -10 && temp < 50) {
        currentTemperature = temp;
        Serial.print("水温: ");
        Serial.print(currentTemperature);
        Serial.println(" °C");
    } else {
        Serial.println("温度传感器读取失败！");
    }
}

void readTDS() {
    // 读取 ADC 值
    int rawValue = analogRead(TDS_PIN);
    
    // 存入滤波缓冲区
    tdsBuffer[tdsBufferIndex] = rawValue;
    tdsBufferIndex = (tdsBufferIndex + 1) % TDS_SAMPLES;
    
    // 获取中值滤波后的值
    int filteredValue = getMedianTDS();
    
    // 转换为电压
    float voltage = filteredValue * VREF / 4095.0;
    
    // 温度补偿系数
    float compensationCoefficient = 1.0 + 0.02 * (currentTemperature - 25.0);
    float compensationVoltage = voltage / compensationCoefficient;
    
    // 转换为 TDS 值 (ppm)
    currentTDS = (133.42 * compensationVoltage * compensationVoltage * compensationVoltage
                 - 255.86 * compensationVoltage * compensationVoltage
                 + 857.39 * compensationVoltage) * TDS_FACTOR;
    
    if (currentTDS < 0) currentTDS = 0;
    
    Serial.print("TDS: ");
    Serial.print(currentTDS);
    Serial.println(" ppm");
}

void readWaterLevel() {
    // XKC-Y25-V: 高电平表示有水，低电平表示缺水
    waterLevel = digitalRead(WATER_LEVEL_PIN);
    
    if (waterLevel == LOW) {
        Serial.println("警告: 水位过低！");
    }
}

// 中值滤波
int getMedianTDS() {
    int sortedBuffer[TDS_SAMPLES];
    memcpy(sortedBuffer, tdsBuffer, sizeof(tdsBuffer));
    
    // 简单冒泡排序
    for (int i = 0; i < TDS_SAMPLES - 1; i++) {
        for (int j = 0; j < TDS_SAMPLES - i - 1; j++) {
            if (sortedBuffer[j] > sortedBuffer[j + 1]) {
                int temp = sortedBuffer[j];
                sortedBuffer[j] = sortedBuffer[j + 1];
                sortedBuffer[j + 1] = temp;
            }
        }
    }
    
    return sortedBuffer[TDS_SAMPLES / 2];
}

// 检查报警条件
void checkAlertConditions() {
    // 温度过高或过低
    if (currentTemperature > 30.0 || currentTemperature < 18.0) {
        alertFlag = true;
    }
    // TDS 过高（水质差）
    else if (currentTDS > 500) {
        alertFlag = true;
    }
    // 水位过低
    else if (waterLevel == LOW) {
        alertFlag = true;
    }
    else {
        alertFlag = false;
    }
}

// ============ HTTP 请求处理 ============
void handleRoot() {
    String html = "<!DOCTYPE html><html><head>";
    html += "<meta charset='UTF-8'>";
    html += "<meta http-equiv='refresh' content='5'>";
    html += "<title>AquaGuard 环境监测</title>";
    html += "<style>body{font-family:Arial;background:#1a1a2e;color:#eee;padding:20px;}";
    html += "h1{color:#00e5ff;}.card{background:#16213e;padding:15px;margin:10px 0;border-radius:10px;}";
    html += ".alert{background:#ff2e63;}.normal{background:#00e5ff;color:#000;}</style></head><body>";
    html += "<h1>🐠 AquaGuard 环境监测</h1>";
    
    html += "<div class='card'><h3>🌡️ 水温</h3>";
    html += "<h2>" + String(currentTemperature, 1) + " °C</h2></div>";
    
    html += "<div class='card'><h3>💧 水质 (TDS)</h3>";
    html += "<h2>" + String(currentTDS) + " ppm</h2>";
    String quality = currentTDS < 150 ? "优" : (currentTDS < 300 ? "良" : "差");
    html += "<p>等级: " + quality + "</p></div>";
    
    html += "<div class='card " + String(waterLevel == HIGH ? "normal" : "alert") + "'>";
    html += "<h3>🚰 水位</h3>";
    html += "<h2>" + String(waterLevel == HIGH ? "正常" : "缺水！") + "</h2></div>";
    
    if (alertFlag) {
        html += "<div class='card alert'><h3>⚠️ 系统警报</h3><p>请检查鱼缸状态！</p></div>";
    }
    
    html += "<p style='color:#666;'>数据每 5 秒自动刷新</p>";
    html += "<p><a href='/status' style='color:#00e5ff;'>查看 JSON 数据</a></p>";
    html += "</body></html>";
    server.send(200, "text/html", html);
}

void handleStatus() {
    unsigned long uptime = (millis() - startTime) / 1000;
    
    String response = "{";
    response += "\"system\":{";
    response += "\"uptime\":" + String(uptime) + ",";
    response += "\"wifi_signal\":" + String(WiFi.RSSI());
    response += "},";
    response += "\"sensors\":{";
    response += "\"temperature\":" + String(currentTemperature, 1) + ",";
    response += "\"tds_value\":" + String(currentTDS) + ",";
    response += "\"water_level\":" + String(waterLevel) + ",";
    response += "\"alert_flag\":" + String(alertFlag ? "true" : "false");
    response += "}}";
    
    server.send(200, "application/json", response);
}

void handleNotFound() {
    server.send(404, "application/json", "{\"error\":\"接口不存在\"}");
}
