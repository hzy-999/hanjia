"""
AquaGuard 韩家家庭智能系统 - API 客户端模块

负责与 ESP32 传感器节点和 ESP8266 灯光节点通信
"""

import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SensorData:
    """传感器数据"""
    temperature: float = 0.0
    tds_value: int = 0
    water_level: int = 1
    alert_flag: bool = False
    uptime: int = 0
    wifi_signal: int = 0


@dataclass
class LightStatus:
    """灯光状态"""
    power: str = "off"
    mode: str = "static"
    color_r: int = 255
    color_g: int = 255
    color_b: int = 255
    wifi_signal: int = 0


class SensorClient:
    """ESP32 传感器节点客户端"""
    
    def __init__(self, ip: str, timeout: float = 3.0):
        """
        初始化传感器客户端
        
        Args:
            ip: 节点 IP 地址（可包含端口号）
            timeout: 请求超时时间（秒）
        """
        self.ip = ip
        self.timeout = timeout
        self.connected = False
        self.last_error = ""
    
    @property
    def base_url(self) -> str:
        """获取基础 URL"""
        if not self.ip.startswith("http"):
            return f"http://{self.ip}"
        return self.ip
    
    def get_status(self) -> Optional[SensorData]:
        """
        获取传感器状态
        
        Returns:
            SensorData 对象，失败返回 None
        """
        try:
            response = requests.get(
                f"{self.base_url}/status",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            self.connected = True
            self.last_error = ""
            
            # 解析响应数据
            system = data.get("system", {})
            sensors = data.get("sensors", {})
            
            return SensorData(
                temperature=sensors.get("temperature", 0.0),
                tds_value=sensors.get("tds_value", 0),
                water_level=sensors.get("water_level", 1),
                alert_flag=sensors.get("alert_flag", False),
                uptime=system.get("uptime", 0),
                wifi_signal=system.get("wifi_signal", 0)
            )
        
        except requests.exceptions.Timeout:
            self.connected = False
            self.last_error = "连接超时"
        except requests.exceptions.ConnectionError:
            self.connected = False
            self.last_error = "无法连接到设备"
        except requests.exceptions.RequestException as e:
            self.connected = False
            self.last_error = f"请求失败: {e}"
        except Exception as e:
            self.connected = False
            self.last_error = f"未知错误: {e}"
        
        return None


class LightClient:
    """ESP8266 灯光节点客户端"""
    
    def __init__(self, ip: str, timeout: float = 3.0):
        """
        初始化灯光客户端
        
        Args:
            ip: 节点 IP 地址（可包含端口号）
            timeout: 请求超时时间（秒）
        """
        self.ip = ip
        self.timeout = timeout
        self.connected = False
        self.last_error = ""
    
    @property
    def base_url(self) -> str:
        """获取基础 URL"""
        if not self.ip.startswith("http"):
            return f"http://{self.ip}"
        return self.ip
    
    def _request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """发送请求"""
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            self.connected = True
            self.last_error = ""
            return response.json()
        
        except requests.exceptions.Timeout:
            self.connected = False
            self.last_error = "连接超时"
        except requests.exceptions.ConnectionError:
            self.connected = False
            self.last_error = "无法连接到设备"
        except requests.exceptions.RequestException as e:
            self.connected = False
            self.last_error = f"请求失败: {e}"
        except Exception as e:
            self.connected = False
            self.last_error = f"未知错误: {e}"
        
        return None
    
    def get_status(self) -> Optional[LightStatus]:
        """获取灯光状态"""
        data = self._request("status")
        if data:
            color = data.get("color", {})
            return LightStatus(
                power=data.get("power", "off"),
                mode=data.get("mode", "static"),
                color_r=color.get("r", 255),
                color_g=color.get("g", 255),
                color_b=color.get("b", 255),
                wifi_signal=data.get("wifi_signal", 0)
            )
        return None
    
    def set_power(self, state: str) -> bool:
        """
        设置开关状态
        
        Args:
            state: "on" 或 "off"
        
        Returns:
            是否成功
        """
        # 兼容简单固件的 /on /off 接口
        endpoint = "on" if state == "on" else "off"
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                timeout=self.timeout
            )
            self.connected = response.status_code == 200
            self.last_error = ""
            return self.connected
        except requests.exceptions.Timeout:
            self.connected = False
            self.last_error = "连接超时"
        except requests.exceptions.ConnectionError:
            self.connected = False
            self.last_error = "无法连接到设备"
        except Exception as e:
            self.connected = False
            self.last_error = f"请求失败: {e}"
        return False
    
    def turn_on(self) -> bool:
        """开灯"""
        return self.set_power("on")
    
    def turn_off(self) -> bool:
        """关灯"""
        return self.set_power("off")
    
    def set_color(self, r: int, g: int, b: int) -> bool:
        """
        设置颜色
        
        Args:
            r: 红色 (0-255)
            g: 绿色 (0-255)
            b: 蓝色 (0-255)
        
        Returns:
            是否成功
        """
        # 确保值在有效范围内
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        result = self._request("color", {"r": r, "g": g, "b": b})
        return result is not None and result.get("success", False)
    
    def set_mode(self, mode: str) -> bool:
        """
        设置模式
        
        Args:
            mode: "static", "rainbow", 或 "breath"
        
        Returns:
            是否成功
        """
        if mode not in ("static", "rainbow", "breath"):
            self.last_error = f"无效的模式: {mode}"
            return False
        
        result = self._request("mode", {"type": mode})
        return result is not None and result.get("success", False)
    
    # ============ 预设场景 ============
    
    def set_daylight_mode(self) -> bool:
        """日光模式 - 纯白高亮"""
        return self.set_color(255, 255, 255) and self.set_mode("static")
    
    def set_moonlight_mode(self) -> bool:
        """月光模式 - 深蓝低亮"""
        return self.set_color(30, 50, 100) and self.set_mode("static")
    
    def set_aurora_mode(self) -> bool:
        """极光模式 - 彩虹渐变"""
        return self.set_mode("rainbow")
