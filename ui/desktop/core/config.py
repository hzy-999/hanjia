"""
AquaGuard 韩家家庭智能系统 - 配置管理模块

负责读取和保存 config.json 配置文件
"""

import json
import os
import sys
import uuid
from typing import Any, Dict, List

# 默认配置 (新版：设备列表格式)
DEFAULT_CONFIG = {
    "devices": [],  # 设备列表
    "settings": {
        "refresh_interval_ms": 3000,
        "max_temp_alert": 30.0,
        "min_temp_alert": 20.0,
        "max_tds_alert": 300
    },
    "schedule": {
        "enable": False,
        "on_time": "09:00",
        "off_time": "23:00"
    },
    "mijia": {
        "enabled": False,
        "auth_path": ".mijia-api-data/auth.json"
    }
}


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为脚本同级目录的 config.json
        """
        if config_path is None:
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                base_dir = os.path.dirname(sys.executable)
            else:
                # Running as script
                # desktop/core/config.py -> desktop/core -> desktop
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "config.json")
        
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"[配置] 已加载配置文件: {self.config_path}")
                # 检查是否需要迁移旧格式
                self._migrate_old_format()
            else:
                print(f"[配置] 配置文件不存在，使用默认配置")
                self.config = DEFAULT_CONFIG.copy()
                self.config["devices"] = []  # 确保是列表
                self.save()
        except json.JSONDecodeError as e:
            print(f"[配置] 配置文件解析失败: {e}，使用默认配置")
            self.config = DEFAULT_CONFIG.copy()
            self.config["devices"] = []
        except Exception as e:
            print(f"[配置] 加载配置失败: {e}，使用默认配置")
            self.config = DEFAULT_CONFIG.copy()
            self.config["devices"] = []
        
        return self.config
    
    def _migrate_old_format(self) -> None:
        """
        迁移旧版配置格式 (字典) 到新版 (列表)
        
        旧格式:
            "devices": {"sensor_node_ip": "...", "light_node_ip": "..."}
        新格式:
            "devices": [{"id": "...", "name": "...", "type": "...", "ip": "..."}]
        """
        devices = self.config.get("devices", {})
        
        # 如果已经是列表，不需要迁移
        if isinstance(devices, list):
            return
        
        # 如果是字典，需要迁移
        if isinstance(devices, dict):
            print("[配置] 检测到旧版配置格式，正在迁移...")
            
            # 备份旧配置
            backup_path = self.config_path + ".bak"
            try:
                import shutil
                shutil.copy2(self.config_path, backup_path)
                print(f"[配置] 已备份旧配置到: {backup_path}")
            except Exception as e:
                print(f"[配置] 备份失败: {e}")
            
            new_devices = []
            
            # 迁移传感器节点
            sensor_ip = devices.get("sensor_node_ip")
            if sensor_ip and sensor_ip != "127.0.0.1:5001":
                new_devices.append({
                    "id": str(uuid.uuid4()),
                    "name": "传感器节点",
                    "type": "sensor",
                    "ip": sensor_ip
                })
            
            # 迁移灯光节点
            light_ip = devices.get("light_node_ip")
            if light_ip and light_ip != "127.0.0.1:5002":
                new_devices.append({
                    "id": str(uuid.uuid4()),
                    "name": "智能灯",
                    "type": "light",
                    "ip": light_ip
                })
            
            self.config["devices"] = new_devices
            self.save()
            print(f"[配置] 迁移完成，共迁移 {len(new_devices)} 个设备")
    
    def save(self) -> bool:
        """保存配置文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"[配置] 配置已保存到: {self.config_path}")
            return True
        except Exception as e:
            print(f"[配置] 保存配置失败: {e}")
            return False
    
    # ============ 设备列表相关 (新版) ============
    
    def get_devices(self) -> List[dict]:
        """获取设备列表"""
        devices = self.config.get("devices", [])
        if isinstance(devices, list):
            return devices
        return []
    
    def set_devices(self, devices: List[dict]) -> None:
        """设置设备列表"""
        self.config["devices"] = devices
    
    def add_device(self, device_dict: dict) -> None:
        """添加设备"""
        devices = self.get_devices()
        devices.append(device_dict)
        self.config["devices"] = devices
    
    def remove_device(self, device_id: str) -> bool:
        """删除设备"""
        devices = self.get_devices()
        for i, d in enumerate(devices):
            if d.get("id") == device_id:
                devices.pop(i)
                self.config["devices"] = devices
                return True
        return False
    
    # ============ 设备 IP 相关 (旧版兼容) ============
    
    def get_sensor_ip(self) -> str:
        """获取传感器节点 IP (兼容旧版，优先从列表获取)"""
        devices = self.get_devices()
        for d in devices:
            if d.get("type") == "sensor":
                return d.get("ip", "127.0.0.1:5001")
        return "127.0.0.1:5001"
    
    def get_light_ip(self) -> str:
        """获取灯光节点 IP (兼容旧版，优先从列表获取)"""
        devices = self.get_devices()
        for d in devices:
            if d.get("type") == "light":
                return d.get("ip", "127.0.0.1:5002")
        return "127.0.0.1:5002"
    
    # ============ 设置相关 ============
    
    def get_refresh_interval(self) -> int:
        """获取刷新间隔（毫秒）"""
        return self.config.get("settings", {}).get("refresh_interval_ms", 3000)
    
    def set_refresh_interval(self, interval_ms: int) -> None:
        """设置刷新间隔"""
        if "settings" not in self.config:
            self.config["settings"] = {}
        self.config["settings"]["refresh_interval_ms"] = interval_ms
    
    def get_temp_alert_range(self) -> tuple:
        """获取温度报警范围 (min, max)"""
        settings = self.config.get("settings", {})
        return (
            settings.get("min_temp_alert", 20.0),
            settings.get("max_temp_alert", 30.0)
        )
    
    def set_temp_alert_range(self, min_temp: float, max_temp: float) -> None:
        """设置温度报警范围"""
        if "settings" not in self.config:
            self.config["settings"] = {}
        self.config["settings"]["min_temp_alert"] = min_temp
        self.config["settings"]["max_temp_alert"] = max_temp
    
    def get_tds_alert(self) -> int:
        """获取 TDS 报警阈值"""
        return self.config.get("settings", {}).get("max_tds_alert", 300)
    
    def set_tds_alert(self, max_tds: int) -> None:
        """设置 TDS 报警阈值"""
        if "settings" not in self.config:
            self.config["settings"] = {}
        self.config["settings"]["max_tds_alert"] = max_tds

    # ============ 鱼缸节点相关 ============

    def get_fish_tank_ip(self) -> str:
        """获取鱼缸节点 IP"""
        return self.config.get("settings", {}).get("fish_tank_ip", "192.168.31.161")

    def set_fish_tank_ip(self, ip: str) -> None:
        """设置鱼缸节点 IP"""
        if "settings" not in self.config:
            self.config["settings"] = {}
        self.config["settings"]["fish_tank_ip"] = ip
    
    # ============ 定时相关 ============
    
    def get_schedule(self) -> dict:
        """获取定时设置"""
        return self.config.get("schedule", {
            "enable": False,
            "on_time": "09:00",
            "off_time": "23:00"
        })
    
    def set_schedule(self, enable: bool, on_time: str, off_time: str) -> None:
        """设置定时"""
        self.config["schedule"] = {
            "enable": enable,
            "on_time": on_time,
            "off_time": off_time
        }
    
    def is_schedule_enabled(self) -> bool:
        """定时是否启用"""
        return self.config.get("schedule", {}).get("enable", False)
    
    # ============ 米家相关 ============
    
    def get_mijia_config(self) -> dict:
        """获取米家配置"""
        return self.config.get("mijia", {
            "enabled": False,
            "auth_path": ".mijia-api-data/auth.json"
        })
    
    def is_mijia_enabled(self) -> bool:
        """米家是否启用"""
        return self.get_mijia_config().get("enabled", False)
    
    def set_mijia_enabled(self, enabled: bool) -> None:
        """设置米家启用状态"""
        if "mijia" not in self.config:
            self.config["mijia"] = {}
        self.config["mijia"]["enabled"] = enabled
    
    def get_mijia_auth_path(self) -> str:
        """获取米家认证文件路径"""
        return self.get_mijia_config().get("auth_path", ".mijia-api-data/auth.json")
    
    def set_mijia_auth_path(self, auth_path: str) -> None:
        """设置米家认证文件路径"""
        if "mijia" not in self.config:
            self.config["mijia"] = {}
        self.config["mijia"]["auth_path"] = auth_path
    
    # ============ 通知相关 ============
    
    def get_notification_config(self) -> dict:
        """获取通知配置"""
        return self.config.get("notification", {
            "enabled": False,
            "token": "",
            "rules": {}  # {device_id: {"on": bool, "off": bool}}
        })
    
    def set_notification_config(self, token: str, enabled: bool) -> None:
        """设置通知配置 (基本)"""
        if "notification" not in self.config:
            self.config["notification"] = {}
        
        # 保留现有的 rules
        current_rules = self.config["notification"].get("rules", {})
        
        self.config["notification"] = {
            "enabled": enabled,
            "token": token,
            "rules": current_rules
        }
        
    def get_notification_rules(self) -> dict:
        """获取通知规则"""
        return self.get_notification_config().get("rules", {})

    def set_notification_rules(self, rules: dict) -> None:
        """设置通知规则"""
        if "notification" not in self.config:
            self.config["notification"] = {
                "enabled": False,
                "token": "",
                "rules": {}
            }
        self.config["notification"]["rules"] = rules

    # ============ 状态变更记录相关 ============
    
    def get_status_log_config(self) -> dict:
        """获取状态记录配置"""
        return self.config.get("status_log", {
            "enabled": False,
            "logs": []
        })
    
    def is_status_log_enabled(self) -> bool:
        """状态记录是否启用"""
        return self.get_status_log_config().get("enabled", False)
    
    def set_status_log_enabled(self, enabled: bool) -> None:
        """设置状态记录启用状态"""
        if "status_log" not in self.config:
            self.config["status_log"] = {"enabled": False, "logs": []}
        self.config["status_log"]["enabled"] = enabled
    
    def get_status_logs(self) -> list:
        """获取状态记录列表"""
        return self.get_status_log_config().get("logs", [])
    
    def add_status_log(self, log: dict) -> None:
        """添加状态记录"""
        if "status_log" not in self.config:
            self.config["status_log"] = {"enabled": True, "logs": []}
        
        logs = self.config["status_log"].get("logs", [])
        # 限制最多保存100条记录
        if len(logs) >= 100:
            logs = logs[-99:]
        logs.append(log)
        self.config["status_log"]["logs"] = logs
        self.save()
    
    def mark_log_read(self, log_id: str) -> None:
        """标记记录为已读"""
        logs = self.get_status_logs()
        for log in logs:
            if log.get("id") == log_id:
                log["read"] = True
                break
        if "status_log" in self.config:
            self.config["status_log"]["logs"] = logs
            self.save()
    
    def mark_all_logs_read(self) -> None:
        """标记所有记录为已读"""
        logs = self.get_status_logs()
        for log in logs:
            log["read"] = True
        if "status_log" in self.config:
            self.config["status_log"]["logs"] = logs
            self.save()
    
    def clear_status_logs(self) -> None:
        """清空状态记录"""
        if "status_log" in self.config:
            self.config["status_log"]["logs"] = []
            self.save()
    
    def get_unread_count(self) -> int:
        """获取未读消息数量"""
        logs = self.get_status_logs()
        return sum(1 for log in logs if not log.get("read", False))


# 全局配置实例
_config_instance = None


def get_config() -> ConfigManager:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
