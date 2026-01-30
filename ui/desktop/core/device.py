"""
AquaGuard 韩家家庭智能系统 - 设备模型模块

定义统一的设备数据结构，支持多种设备类型
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class DeviceType(Enum):
    """设备类型枚举"""
    LIGHT = "light"             # 灯 (ESP8266)
    SENSOR = "sensor"           # 传感器 (ESP32)
    SWITCH = "switch"           # 插座/开关 (未来扩展)
    MIJIA = "mijia"             # 米家通用设备
    MIJIA_LIGHT = "mijia_light" # 米家智能灯
    MIJIA_SWITCH = "mijia_switch"  # 米家智能开关/插座
    MIJIA_FAN = "mijia_fan"     # 米家风扇
    MIJIA_SENSOR = "mijia_sensor"  # 米家传感器


# 设备类型对应的图标和颜色
DEVICE_TYPE_INFO = {
    DeviceType.LIGHT: {
        "icon": "💡",
        "color": "#FFD700",
        "name": "智能灯"
    },
    DeviceType.SENSOR: {
        "icon": "🌡️",
        "color": "#00CED1",
        "name": "传感器"
    },
    DeviceType.SWITCH: {
        "icon": "🔌",
        "color": "#32CD32",
        "name": "智能插座"
    },
    DeviceType.MIJIA: {
        "icon": "📱",
        "color": "#FF6600",
        "name": "米家设备"
    },
    DeviceType.MIJIA_LIGHT: {
        "icon": "💡",
        "color": "#FF9500",
        "name": "米家智能灯"
    },
    DeviceType.MIJIA_SWITCH: {
        "icon": "🔌",
        "color": "#FF6600",
        "name": "米家开关"
    },
    DeviceType.MIJIA_FAN: {
        "icon": "🌀",
        "color": "#00BFFF",
        "name": "米家风扇"
    },
    DeviceType.MIJIA_SENSOR: {
        "icon": "🌡️",
        "color": "#00CED1",
        "name": "米家传感器"
    }
}


@dataclass
class Device:
    """
    设备数据模型
    
    Attributes:
        id: 设备唯一标识 (UUID)
        name: 用户自定义名称
        type: 设备类型
        ip: 设备 IP 地址
        online: 是否在线
        last_seen: 最后一次检测到在线的时间
        data: 设备特定的状态数据 (如灯的颜色、传感器的温度等)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "未命名设备"
    type: DeviceType = DeviceType.LIGHT
    ip: str = ""
    did: str = ""  # 米家设备 ID
    model: str = ""  # 设备型号 (米家设备)
    online: bool = False
    visible: bool = True  # 是否在首页显示
    last_seen: Optional[datetime] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    # 连接失败计数 (用于离线检测)
    _fail_count: int = field(default=0, repr=False)
    
    def to_dict(self) -> dict:
        """
        序列化为字典 (用于保存到 config.json)
        
        Returns:
            包含设备信息的字典
        """
        result = {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "ip": self.ip,
            "visible": self.visible  # 保存可见性设置
        }
        # 米家设备额外保存 did 和 model
        if self.did:
            result["did"] = self.did
        if self.model:
            result["model"] = self.model
        # 保存设备状态数据 (缓存最后状态)
        if self.data:
            result["data"] = self.data
        return result
    
    @classmethod
    def from_dict(cls, d: dict) -> "Device":
        """
        从字典反序列化
        
        Args:
            d: 包含设备信息的字典
            
        Returns:
            Device 实例
        """
        device_type = d.get("type", "light")
        
        # 兼容处理：确保类型有效
        try:
            dtype = DeviceType(device_type)
        except ValueError:
            dtype = DeviceType.LIGHT
            
        return cls(
            id=d.get("id", str(uuid.uuid4())),
            name=d.get("name", "未命名设备"),
            type=dtype,
            ip=d.get("ip", ""),
            did=d.get("did", ""),
            model=d.get("model", ""),
            visible=d.get("visible", True),  # 默认可见
            data=d.get("data", {})  # 恢复状态数据
        )
    
    @property
    def icon(self) -> str:
        """获取设备图标"""
        return DEVICE_TYPE_INFO.get(self.type, {}).get("icon", "📦")
    
    @property
    def color(self) -> str:
        """获取设备主题色"""
        return DEVICE_TYPE_INFO.get(self.type, {}).get("color", "#888888")
    
    @property
    def type_name(self) -> str:
        """获取设备类型名称"""
        return DEVICE_TYPE_INFO.get(self.type, {}).get("name", "未知设备")
    
    def mark_online(self) -> None:
        """标记设备在线"""
        self.online = True
        self.last_seen = datetime.now()
        self._fail_count = 0
    
    def mark_failed(self, max_fails: int = 3) -> None:
        """
        标记一次连接失败
        
        Args:
            max_fails: 连续失败多少次后标记为离线
        """
        self._fail_count += 1
        if self._fail_count >= max_fails:
            self.online = False
    
    def get_status_text(self) -> str:
        """
        获取状态文本 (用于 UI 显示)
        
        Returns:
            状态描述字符串
        """
        if not self.online:
            return "离线"
        
        # ESP 灯光设备
        if self.type == DeviceType.LIGHT:
            power = self.data.get("power", "off")
            return "已开启" if power == "on" else "已关闭"
        
        # ESP 传感器设备
        elif self.type == DeviceType.SENSOR:
            temp = self.data.get("temperature")
            if temp is not None:
                return f"{temp:.1f}°C"
            return "在线"
        
        # 米家灯光/开关/风扇设备
        elif self.type in (DeviceType.MIJIA_LIGHT, DeviceType.MIJIA_SWITCH, DeviceType.MIJIA_FAN):
            power = self.data.get("power", "off")
            if power == "on":
                brightness = self.data.get("brightness")
                if brightness is not None:
                    return f"已开启 ({brightness}%)"
                return "已开启"
            return "已关闭"
        
        # 米家传感器
        elif self.type == DeviceType.MIJIA_SENSOR:
            temp = self.data.get("temperature")
            if temp is not None:
                return f"{temp:.1f}°C"
            return "在线"
        
        
        # 米家通用设备
        elif self.type == DeviceType.MIJIA:
            # 检查是否有净化器数据 (Temp, Hum, PM2.5)
            # 只要有任意一个数据，就认为是净化器并显示
            has_sensor_data = False
            parts = []
            
            # 检查是否有净化器特征属性
            is_purifier = "pm25" in self.data or "filter_life" in self.data or "air_quality" in self.data
            
            if is_purifier:
                # 温度
                temp = self.data.get("temperature")
                if temp is not None:
                    parts.append(f"{temp}℃")
                else:
                    parts.append("--℃")
                    
                # 湿度
                hum = self.data.get("humidity")
                if hum is not None:
                    parts.append(f"{hum}%")
                else:
                    parts.append("--%")
                    
                # PM2.5
                pm25 = self.data.get("pm25")
                if pm25 is not None:
                    parts.append(f"PM2.5 {pm25}")
                else:
                    parts.append("PM2.5 --")
                
                if parts:
                    return " | ".join(parts)
            
            # 普通米家设备
            power = self.data.get("power")
            if power is not None:
                return "已开启" if power == "on" else "已关闭"
            return "在线"
        
        return "在线"
    
    @property
    def is_mijia(self) -> bool:
        """是否为米家设备"""
        return self.type in (
            DeviceType.MIJIA,
            DeviceType.MIJIA_LIGHT,
            DeviceType.MIJIA_SWITCH,
            DeviceType.MIJIA_FAN,
            DeviceType.MIJIA_SENSOR
        )
