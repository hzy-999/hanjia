/**
 * AquaGuard 韩家家庭智能系统 - ESP8266 氛围控制节点
 * 
 * 功能：
 * - 控制 WS2812B RGB 灯带
 * - 提供 RESTful API 接口
 * - 支持静态颜色、彩虹渐变、呼吸效果
 * 
 * 接口：
 * - GET /power?state=on|off    开关控制
 * - GET /color?r=&g=&b=        颜色设定
 * - GET /mode?type=rainbow|breath|static  模式切换
 * - GET /status                获取当前状态
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <Adafruit_NeoPixel.h>

// ============ Wi-Fi 配置 ============
const char* ssid = "YOUR_WIFI_SSID";      // 修改为您的 Wi-Fi 名称
const char* password = "YOUR_WIFI_PASSWORD"; // 修改为您的 Wi-Fi 密码

// ============ 灯带配置 ============
#define LED_PIN     D2      // GPIO 4
#define LED_COUNT   1       // LED 数量

// ============ 全局变量 ============
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
ESP8266WebServer server(80);

// 当前状态
bool powerState = false;           // 开关状态
uint8_t currentR = 255;            // 当前红色值
uint8_t currentG = 255;            // 当前绿色值
uint8_t currentB = 255;            // 当前蓝色值
String currentMode = "static";     // 当前模式: static, rainbow, breath

// 动画变量
unsigned long lastUpdate = 0;
int animationStep = 0;
int breathDirection = 1;
int breathBrightness = 0;

// ============ 函数声明 ============
void handleRoot();
void handlePower();
void handleColor();
void handleMode();
void handleStatus();
void handleNotFound();
void updateLED();
void applyStaticColor();
void applyRainbowEffect();
void applyBreathEffect();
uint32_t colorWheel(byte wheelPos);

// ============ 初始化 ============
void setup() {
    Serial.begin(115200);
    Serial.println("\n\n=== AquaGuard ESP8266 氛围控制节点 ===");
    
    // 初始化灯带
    strip.begin();
    strip.show();
    strip.setBrightness(255);
    
    // 连接 Wi-Fi
    Serial.print("连接 Wi-Fi: ");
    Serial.println(ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        // 连接时显示青色呼吸效果
        int brightness = (sin(attempts * 0.3) + 1) * 127;
        strip.setPixelColor(0, strip.Color(0, brightness, brightness));
        strip.show();
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWi-Fi 连接成功！");
        Serial.print("IP 地址: ");
        Serial.println(WiFi.localIP());
        
        // 连接成功显示绿色
        strip.setPixelColor(0, strip.Color(0, 255, 0));
        strip.show();
        delay(1000);
    } else {
        Serial.println("\nWi-Fi 连接失败！");
        // 连接失败显示红色
        strip.setPixelColor(0, strip.Color(255, 0, 0));
        strip.show();
    }
    
    // 配置 HTTP 服务器路由
    server.on("/", handleRoot);
    server.on("/power", handlePower);
    server.on("/color", handleColor);
    server.on("/mode", handleMode);
    server.on("/status", handleStatus);
    server.onNotFound(handleNotFound);
    
    // 启动服务器
    server.begin();
    Serial.println("HTTP 服务器已启动");
    
    // 初始化完成，关闭灯
    strip.setPixelColor(0, strip.Color(0, 0, 0));
    strip.show();
}

// ============ 主循环 ============
void loop() {
    server.handleClient();
    updateLED();
}

// ============ LED 更新逻辑 ============
void updateLED() {
    if (!powerState) {
        strip.setPixelColor(0, strip.Color(0, 0, 0));
        strip.show();
        return;
    }
    
    if (currentMode == "static") {
        applyStaticColor();
    } else if (currentMode == "rainbow") {
        applyRainbowEffect();
    } else if (currentMode == "breath") {
        applyBreathEffect();
    }
}

void applyStaticColor() {
    strip.setPixelColor(0, strip.Color(currentR, currentG, currentB));
    strip.show();
}

void applyRainbowEffect() {
    unsigned long currentTime = millis();
    if (currentTime - lastUpdate >= 50) {
        lastUpdate = currentTime;
        animationStep = (animationStep + 1) % 256;
        
        for (int i = 0; i < LED_COUNT; i++) {
            strip.setPixelColor(i, colorWheel((i * 256 / LED_COUNT + animationStep) & 255));
        }
        strip.show();
    }
}

void applyBreathEffect() {
    unsigned long currentTime = millis();
    if (currentTime - lastUpdate >= 20) {
        lastUpdate = currentTime;
        
        breathBrightness += breathDirection * 5;
        if (breathBrightness >= 255) {
            breathBrightness = 255;
            breathDirection = -1;
        } else if (breathBrightness <= 0) {
            breathBrightness = 0;
            breathDirection = 1;
        }
        
        uint8_t r = (currentR * breathBrightness) / 255;
        uint8_t g = (currentG * breathBrightness) / 255;
        uint8_t b = (currentB * breathBrightness) / 255;
        strip.setPixelColor(0, strip.Color(r, g, b));
        strip.show();
    }
}

// 色轮函数，用于彩虹效果
uint32_t colorWheel(byte wheelPos) {
    wheelPos = 255 - wheelPos;
    if (wheelPos < 85) {
        return strip.Color(255 - wheelPos * 3, 0, wheelPos * 3);
    }
    if (wheelPos < 170) {
        wheelPos -= 85;
        return strip.Color(0, wheelPos * 3, 255 - wheelPos * 3);
    }
    wheelPos -= 170;
    return strip.Color(wheelPos * 3, 255 - wheelPos * 3, 0);
}

// ============ HTTP 请求处理 ============
void handleRoot() {
    String html = "<!DOCTYPE html><html><head>";
    html += "<meta charset='UTF-8'>";
    html += "<title>AquaGuard 灯光控制</title>";
    html += "<style>body{font-family:Arial;background:#1a1a2e;color:#eee;padding:20px;}";
    html += "h1{color:#00e5ff;}a{color:#00e5ff;}</style></head><body>";
    html += "<h1>🐠 AquaGuard 灯光控制</h1>";
    html += "<p>状态: " + String(powerState ? "开启" : "关闭") + "</p>";
    html += "<p>模式: " + currentMode + "</p>";
    html += "<p>颜色: R=" + String(currentR) + " G=" + String(currentG) + " B=" + String(currentB) + "</p>";
    html += "<h2>API 接口</h2>";
    html += "<ul>";
    html += "<li><a href='/power?state=on'>开灯</a></li>";
    html += "<li><a href='/power?state=off'>关灯</a></li>";
    html += "<li><a href='/color?r=255&g=0&b=0'>红色</a></li>";
    html += "<li><a href='/color?r=0&g=255&b=0'>绿色</a></li>";
    html += "<li><a href='/color?r=0&g=0&b=255'>蓝色</a></li>";
    html += "<li><a href='/mode?type=static'>静态模式</a></li>";
    html += "<li><a href='/mode?type=rainbow'>彩虹模式</a></li>";
    html += "<li><a href='/mode?type=breath'>呼吸模式</a></li>";
    html += "<li><a href='/status'>状态查询</a></li>";
    html += "</ul></body></html>";
    server.send(200, "text/html", html);
}

void handlePower() {
    String state = server.arg("state");
    if (state == "on") {
        powerState = true;
        server.send(200, "application/json", "{\"success\":true,\"power\":\"on\"}");
    } else if (state == "off") {
        powerState = false;
        server.send(200, "application/json", "{\"success\":true,\"power\":\"off\"}");
    } else {
        server.send(400, "application/json", "{\"error\":\"无效的状态参数，请使用 on 或 off\"}");
    }
}

void handleColor() {
    if (server.hasArg("r") && server.hasArg("g") && server.hasArg("b")) {
        currentR = constrain(server.arg("r").toInt(), 0, 255);
        currentG = constrain(server.arg("g").toInt(), 0, 255);
        currentB = constrain(server.arg("b").toInt(), 0, 255);
        
        String response = "{\"success\":true,\"color\":{\"r\":";
        response += String(currentR) + ",\"g\":" + String(currentG);
        response += ",\"b\":" + String(currentB) + "}}";
        server.send(200, "application/json", response);
    } else {
        server.send(400, "application/json", "{\"error\":\"缺少 r, g, b 参数\"}");
    }
}

void handleMode() {
    String type = server.arg("type");
    if (type == "static" || type == "rainbow" || type == "breath") {
        currentMode = type;
        animationStep = 0;
        breathBrightness = 0;
        breathDirection = 1;
        server.send(200, "application/json", "{\"success\":true,\"mode\":\"" + type + "\"}");
    } else {
        server.send(400, "application/json", "{\"error\":\"无效的模式，请使用 static, rainbow 或 breath\"}");
    }
}

void handleStatus() {
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

void handleNotFound() {
    server.send(404, "application/json", "{\"error\":\"接口不存在\"}");
}
