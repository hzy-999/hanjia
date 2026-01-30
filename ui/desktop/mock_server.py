"""
AquaGuard 韩家家庭智能系统 - 模拟服务器

用于在没有硬件时测试桌面应用程序
模拟 ESP32 传感器节点和 ESP8266 灯光节点

使用方法：
    python mock_server.py

传感器节点：http://127.0.0.1:5001
灯光节点：http://127.0.0.1:5002
"""

from flask import Flask, request, jsonify
import threading
import random
import time
import math

# ============ 传感器节点模拟 ============

sensor_app = Flask("SensorNode")

# 模拟数据
sensor_state = {
    "start_time": time.time(),
    "temperature": 25.0,
    "tds_value": 120,
    "water_level": 1,
    "alert_flag": False
}

def update_sensor_data():
    """后台更新模拟传感器数据"""
    while True:
        # 模拟温度波动 (24-27°C)
        sensor_state["temperature"] = 25.5 + math.sin(time.time() / 30) * 1.5 + random.uniform(-0.3, 0.3)
        sensor_state["temperature"] = round(sensor_state["temperature"], 1)
        
        # 模拟 TDS 波动 (100-160 ppm)
        sensor_state["tds_value"] = int(130 + math.sin(time.time() / 60) * 30 + random.randint(-10, 10))
        
        # 偶尔模拟低水位
        if random.random() < 0.02:  # 2% 概率
            sensor_state["water_level"] = 0
        else:
            sensor_state["water_level"] = 1
        
        # 更新报警标志
        sensor_state["alert_flag"] = (
            sensor_state["temperature"] > 30 or 
            sensor_state["temperature"] < 18 or
            sensor_state["tds_value"] > 300 or
            sensor_state["water_level"] == 0
        )
        
        time.sleep(2)

@sensor_app.route("/")
def sensor_index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ESP32 模拟器</title>
        <meta http-equiv="refresh" content="3">
        <style>
            body { font-family: Arial; background: #1a1a2e; color: #eee; padding: 20px; }
            h1 { color: #00e5ff; }
            .card { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 10px; }
        </style>
    </head>
    <body>
        <h1>🔧 ESP32 传感器节点 (模拟器)</h1>
        <div class="card">
            <h3>🌡️ 水温: """ + f"{sensor_state['temperature']:.1f}" + """ °C</h3>
        </div>
        <div class="card">
            <h3>💧 TDS: """ + str(sensor_state['tds_value']) + """ ppm</h3>
        </div>
        <div class="card">
            <h3>🚰 水位: """ + ("正常" if sensor_state['water_level'] == 1 else "缺水") + """</h3>
        </div>
        <p style="color: #666;">数据每 3 秒自动刷新</p>
    </body>
    </html>
    """

@sensor_app.route("/status")
def sensor_status():
    uptime = int(time.time() - sensor_state["start_time"])
    
    return jsonify({
        "system": {
            "uptime": uptime,
            "wifi_signal": -45 + random.randint(-5, 5)
        },
        "sensors": {
            "temperature": sensor_state["temperature"],
            "tds_value": sensor_state["tds_value"],
            "water_level": sensor_state["water_level"],
            "alert_flag": sensor_state["alert_flag"]
        }
    })


# ============ 灯光节点模拟 ============

light_app = Flask("LightNode")

# 模拟灯光状态
light_state = {
    "power": "off",
    "mode": "static",
    "color": {"r": 255, "g": 255, "b": 255}
}

@light_app.route("/")
def light_index():
    color = light_state["color"]
    hex_color = f"#{color['r']:02x}{color['g']:02x}{color['b']:02x}"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ESP8266 模拟器</title>
        <style>
            body {{ font-family: Arial; background: #1a1a2e; color: #eee; padding: 20px; }}
            h1 {{ color: #00e5ff; }}
            .card {{ background: #16213e; padding: 15px; margin: 10px 0; border-radius: 10px; }}
            .preview {{ width: 100px; height: 100px; border-radius: 50%; margin: 10px auto; }}
            a {{ color: #00e5ff; }}
        </style>
    </head>
    <body>
        <h1>🔧 ESP8266 灯光节点 (模拟器)</h1>
        <div class="card">
            <h3>状态: {light_state['power']}</h3>
            <h3>模式: {light_state['mode']}</h3>
            <h3>颜色: RGB({color['r']}, {color['g']}, {color['b']})</h3>
            <div class="preview" style="background: {hex_color if light_state['power'] == 'on' else '#333'};"></div>
        </div>
        <h2>控制面板</h2>
        <ul>
            <li><a href="/power?state=on">开灯</a></li>
            <li><a href="/power?state=off">关灯</a></li>
            <li><a href="/color?r=255&g=0&b=0">红色</a></li>
            <li><a href="/color?r=0&g=255&b=0">绿色</a></li>
            <li><a href="/color?r=0&g=0&b=255">蓝色</a></li>
            <li><a href="/mode?type=rainbow">彩虹模式</a></li>
            <li><a href="/mode?type=breath">呼吸模式</a></li>
            <li><a href="/mode?type=static">静态模式</a></li>
        </ul>
    </body>
    </html>
    """

@light_app.route("/power")
def light_power():
    state = request.args.get("state", "").lower()
    if state in ["on", "off"]:
        light_state["power"] = state
        return jsonify({"success": True, "power": state})
    return jsonify({"error": "无效的状态参数"}), 400

@light_app.route("/color")
def light_color():
    try:
        r = int(request.args.get("r", 255))
        g = int(request.args.get("g", 255))
        b = int(request.args.get("b", 255))
        
        light_state["color"] = {
            "r": max(0, min(255, r)),
            "g": max(0, min(255, g)),
            "b": max(0, min(255, b))
        }
        
        return jsonify({"success": True, "color": light_state["color"]})
    except ValueError:
        return jsonify({"error": "无效的颜色参数"}), 400

@light_app.route("/mode")
def light_mode():
    mode_type = request.args.get("type", "").lower()
    if mode_type in ["static", "rainbow", "breath"]:
        light_state["mode"] = mode_type
        return jsonify({"success": True, "mode": mode_type})
    return jsonify({"error": "无效的模式"}), 400

@light_app.route("/status")
def light_status():
    return jsonify({
        "power": light_state["power"],
        "mode": light_state["mode"],
        "color": light_state["color"],
        "wifi_signal": -42 + random.randint(-5, 5)
    })


# ============ 启动服务器 ============

def run_sensor_server():
    """运行传感器服务器"""
    print("[传感器节点] 启动在 http://127.0.0.1:5001")
    sensor_app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)

def run_light_server():
    """运行灯光服务器"""
    print("[灯光节点] 启动在 http://127.0.0.1:5002")
    light_app.run(host="127.0.0.1", port=5002, debug=False, use_reloader=False)


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 AquaGuard 模拟服务器")
    print("=" * 60)
    print()
    print("此服务器用于在没有实际硬件时测试桌面应用程序。")
    print()
    print("模拟节点地址：")
    print("  📡 传感器节点 (ESP32): http://127.0.0.1:5001")
    print("  💡 灯光节点 (ESP8266): http://127.0.0.1:5002")
    print()
    print("请在桌面应用的设置中将 IP 地址配置为上述地址。")
    print()
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()
    
    # 启动传感器数据更新线程
    update_thread = threading.Thread(target=update_sensor_data, daemon=True)
    update_thread.start()
    
    # 启动两个服务器
    sensor_thread = threading.Thread(target=run_sensor_server, daemon=True)
    light_thread = threading.Thread(target=run_light_server, daemon=True)
    
    sensor_thread.start()
    light_thread.start()
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n服务器已停止")
