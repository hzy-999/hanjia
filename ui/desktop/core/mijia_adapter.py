"""
AquaGuard 韩家家庭智能系统 - 米家 API 适配层

封装 mijiaAPI 库，提供与设备管理器兼容的接口
"""

import threading
import io
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from dataclasses import dataclass

try:
    from mijiaAPI import mijiaAPI, mijiaDevice
    from mijiaAPI.errors import (
        LoginError,
        DeviceNotFoundError,
        DeviceGetError,
        DeviceSetError,
        APIError,
    )
    MIJIA_AVAILABLE = True
except ImportError:
    MIJIA_AVAILABLE = False
    # 定义占位异常
    LoginError = Exception
    DeviceNotFoundError = Exception
    DeviceGetError = Exception
    DeviceSetError = Exception
    APIError = Exception

try:
    import qrcode
    from PIL import Image
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


@dataclass
class MijiaDeviceInfo:
    """米家设备信息"""
    did: str                    # 设备 ID
    name: str                   # 设备名称
    model: str                  # 设备型号
    is_online: bool = True      # 是否在线
    icon: str = "📱"            # 图标
    category: str = "other"     # 设备类别 (light, switch, sensor, other)


class MijiaAdapter:
    """
    米家 API 适配器
    
    负责管理米家账户登录状态和设备操作
    """
    
    def __init__(self, auth_path: Optional[str] = None):
        """
        初始化适配器
        
        Args:
            auth_path: 认证文件路径，默认使用 .mijia-api-data/auth.json
        """
        self._auth_path = auth_path or ".mijia-api-data/auth.json"
        self._api: Optional['mijiaAPI'] = None
        self._devices: Dict[str, 'mijiaDevice'] = {}  # did -> mijiaDevice
        self._device_info_cache: Dict[str, MijiaDeviceInfo] = {}
        self._login_callback: Optional[Callable[[bool, str], None]] = None
        self._lock = threading.Lock()
        
        # 检查是否可用
        if not MIJIA_AVAILABLE:
            print("[MijiaAdapter] 警告: mijiaAPI 库未安装，米家功能不可用")
        else:
            # 尝试从已保存的认证文件恢复登录状态
            self._try_restore_auth()
    
    @property
    def is_available(self) -> bool:
        """检查 mijiaAPI 是否可用"""
        return MIJIA_AVAILABLE
    
    def _try_restore_auth(self) -> None:
        """
        尝试从已保存的认证文件恢复登录状态
        """
        try:
            from pathlib import Path
            auth_file = Path(self._auth_path)
            
            if auth_file.exists():
                # 初始化 API 并检查是否有效
                self._api = mijiaAPI(self._auth_path)
                if self._api.available:
                    print(f"[MijiaAdapter] 已恢复米家登录状态")
                else:
                    print(f"[MijiaAdapter] 认证文件存在但已过期，需要重新登录")
                    self._api = None
            else:
                print(f"[MijiaAdapter] 未找到认证文件，需要首次登录")
        except Exception as e:
            print(f"[MijiaAdapter] 恢复认证状态失败: {e}")
            self._api = None
    
    @property
    def is_logged_in(self) -> bool:
        """检查是否已登录（使用缓存，不触发网络请求）"""
        if not self._api:
            return False
        # 只检查 auth_data 是否存在关键字段，不调用 available（会触发网络请求）
        try:
            auth_data = self._api.auth_data
            required_keys = ["ssecurity", "userId", "serviceToken"]
            return all(key in auth_data for key in required_keys)
        except Exception:
            return False
    
    def set_login_callback(self, callback: Callable[[bool, str], None]) -> None:
        """
        设置登录回调
        
        Args:
            callback: 登录完成回调，参数为 (是否成功, 消息)
        """
        self._login_callback = callback
    
    def get_qr_image(self) -> Optional['Image.Image']:
        """
        获取登录二维码图片
        
        Returns:
            PIL Image 对象，失败返回 None
        """
        if not MIJIA_AVAILABLE or not QRCODE_AVAILABLE:
            return None
        
        try:
            import requests
            from urllib import parse
            import time as time_module
            
            # 初始化 API
            self._api = mijiaAPI(self._auth_path)
            
            # 如果已经登录，直接返回 None
            if self._api.available:
                return None
            
            # Step 1: 获取 location_data (复用 mijiaAPI 的逻辑)
            headers = {
                "User-Agent": self._api.user_agent,
                "Connection": "keep-alive",
                "Accept-Encoding": "gzip",
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": f"deviceId={self._api.deviceId};pass_o={self._api.pass_o};uLocale={self._api.locale};",
            }
            
            service_login_url = f"https://account.xiaomi.com/pass/serviceLogin?_json=true&sid=mijia&_locale={self._api.locale}"
            service_ret = requests.get(service_login_url, headers=headers, timeout=10)
            service_text = service_ret.text.replace("&&&START&&&", "")
            service_data = __import__('json').loads(service_text)
            
            # 从 location 中提取参数
            location = service_data.get("location", "")
            if not location:
                print("[MijiaAdapter] 无法获取登录 location")
                return None
            
            location_data = {k: v[0] for k, v in parse.parse_qs(parse.urlparse(location).query).items()}
            
            # Step 2: 获取二维码
            location_data.update({
                "theme": "",
                "bizDeviceType": "",
                "_hasLogo": "false",
                "_qrsize": "240",
                "_dc": str(int(time_module.time() * 1000)),
            })
            
            login_url = "https://account.xiaomi.com/longPolling/loginUrl?" + parse.urlencode(location_data)
            login_ret = requests.get(login_url, headers=headers, timeout=10, verify=False)
            login_text = login_ret.text.replace("&&&START&&&", "")
            login_data = __import__('json').loads(login_text)
            
            if "loginUrl" not in login_data:
                print(f"[MijiaAdapter] 登录响应中缺少 loginUrl: {login_data}")
                return None
            
            qr_url = login_data["loginUrl"]
            
            # 保存轮询所需数据
            self._lp_url = login_data.get("lp")
            self._login_headers = headers
            
            # 生成二维码图片
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=2,
            )
            qr.add_data(qr_url)
            qr.make(fit=True)
            
            print(f"[MijiaAdapter] 二维码获取成功，也可访问: {login_data.get('qr', '')}")
            return qr.make_image(fill_color="black", back_color="white")
            
        except Exception as e:
            print(f"[MijiaAdapter] 获取二维码失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def start_login_polling(self) -> None:
        """
        开始轮询登录状态 (在后台线程中)
        """
        def poll():
            try:
                import requests
                import time as time_module
                
                if not hasattr(self, '_lp_url') or not self._lp_url:
                    if self._login_callback:
                        self._login_callback(False, "登录 URL 无效")
                    return
                
                print("[MijiaAdapter] 开始轮询登录状态...")
                
                try:
                    # 长轮询等待扫码 (最长 120 秒)
                    session = requests.Session()
                    lp_ret = session.get(self._lp_url, headers=self._login_headers, timeout=120)
                    lp_text = lp_ret.text.replace("&&&START&&&", "")
                    lp_data = __import__('json').loads(lp_text)
                    
                    if lp_data.get("code", -1) != 0:
                        if self._login_callback:
                            self._login_callback(False, lp_data.get("desc", "登录失败"))
                        return
                    
                    # 登录成功，保存认证数据（使用与后端相同的方式）
                    auth_keys = ["psecurity", "nonce", "ssecurity", "passToken", "userId", "cUserId"]
                    for key in auth_keys:
                        if key in lp_data:
                            self._api.auth_data[key] = lp_data[key]
                    
                    # 获取 serviceToken
                    callback_url = lp_data.get("location", "")
                    if callback_url:
                        session.get(callback_url, headers=self._login_headers)
                        cookies = session.cookies.get_dict()
                        self._api.auth_data.update(cookies)
                    
                    # 设置过期时间 (30天)
                    from datetime import datetime, timedelta
                    self._api.auth_data["expireTime"] = int((datetime.now() + timedelta(days=30)).timestamp() * 1000)
                    
                    # 保存并初始化
                    self._api._save_auth_data()
                    self._api._init_session()
                    
                    print("[MijiaAdapter] 登录成功！")
                    if self._login_callback:
                        self._login_callback(True, "登录成功")
                        
                except requests.exceptions.Timeout:
                    if self._login_callback:
                        self._login_callback(False, "登录超时，请重试")
                    
            except Exception as e:
                print(f"[MijiaAdapter] 登录轮询失败: {e}")
                import traceback
                traceback.print_exc()
                if self._login_callback:
                    self._login_callback(False, f"登录失败: {e}")
        
        threading.Thread(target=poll, daemon=True).start()
    
    def login_sync(self) -> bool:
        """
        同步登录 (使用现有认证或终端二维码)
        
        Returns:
            是否登录成功
        """
        if not MIJIA_AVAILABLE:
            return False
        
        try:
            self._api = mijiaAPI(self._auth_path)
            self._api.login()
            return self._api.available
        except Exception as e:
            print(f"[MijiaAdapter] 登录失败: {e}")
            return False
    
    def logout(self) -> None:
        """登出"""
        self._api = None
        self._devices.clear()
        self._device_info_cache.clear()
    
    def get_devices(self) -> List[MijiaDeviceInfo]:
        """
        获取米家设备列表
        
        Returns:
            设备信息列表
        """
        if not self.is_logged_in:
            return []
        
        try:
            devices = self._api.get_devices_list()
            # print(f"[MijiaAdapter DEBUG] 获取到 {len(devices)} 个设备")
            result = []
            
            for d in devices:
                did = d.get("did", "")
                name = d.get("name", "未知设备")
                model = d.get("model", "")
                is_online = d.get("isOnline", True)
                
                # 调试输出每个设备的状态
                # print(f"[MijiaAdapter DEBUG] 设备: {name}, DID: {did}, isOnline: {is_online}, model: {model}")
                

                
                # 根据 model 推断设备类别
                category, icon = self._infer_device_category(model, name)
                
                info = MijiaDeviceInfo(
                    did=did,
                    name=name,
                    model=model,
                    is_online=is_online,
                    icon=icon,
                    category=category
                )
                
                self._device_info_cache[did] = info
                result.append(info)
            
            return result
            
        except Exception as e:
            print(f"[MijiaAdapter] 获取设备列表失败: {e}")
            return []
    
    def _infer_device_category(self, model: str, name: str) -> tuple:
        """
        根据型号和名称推断设备类别
        
        Returns:
            (category, icon)
        """
        model_lower = model.lower()
        name_lower = name.lower()
        
        # 灯具
        if any(kw in model_lower for kw in ["light", "lamp", "bulb", "yeelink"]):
            return "light", "💡"
        if any(kw in name_lower for kw in ["灯", "台灯", "吸顶灯", "床头灯"]):
            return "light", "💡"
        
        # 开关/插座
        if any(kw in model_lower for kw in ["switch", "plug", "outlet", "socket"]):
            return "switch", "🔌"
        if any(kw in name_lower for kw in ["插座", "开关", "排插"]):
            return "switch", "🔌"
        
        # 传感器
        if any(kw in model_lower for kw in ["sensor", "temp", "humid"]):
            return "sensor", "🌡️"
        if any(kw in name_lower for kw in ["传感器", "温度", "湿度"]):
            return "sensor", "🌡️"
        
        # 风扇/空调
        if any(kw in model_lower for kw in ["fan", "aircon", "hvac"]):
            return "fan", "🌀"
        if any(kw in name_lower for kw in ["风扇", "空调", "电风扇"]):
            return "fan", "🌀"
        
        # 净化器
        if any(kw in model_lower for kw in ["purifier", "airpurifier", "airp"]):
            return "purifier", "🌬️"
        if any(kw in name_lower for kw in ["净化器", "空气净化", "purifier"]):
            return "purifier", "🌬️"
        
        return "other", "📱"
    
    def get_mijia_device(self, did: str) -> Optional['mijiaDevice']:
        """
        获取 mijiaDevice 实例
        
        Args:
            did: 设备 ID
            
        Returns:
            mijiaDevice 实例，失败返回 None
        """
        if not self.is_logged_in:
            return None
        
        with self._lock:
            if did in self._devices:
                return self._devices[did]
            
            # 如果是虚拟设备，使用父设备 ID 创建实例(为了获取规格)，但后续操作需要特殊处理
            real_did = did
            if self._is_virtual_did(did):
                real_did = did.split(".")[0]
            
            try:
                device = mijiaDevice(self._api, did=real_did)
                self._devices[did] = device
                return device
            except Exception as e:
                print(f"[MijiaAdapter] 获取设备失败 ({did}): {e}")
                return None
    
    def _is_virtual_did(self, did: str) -> bool:
        """检查是否为虚拟设备ID (如 12345.s1)"""
        return "." in did and ".s" in did
        
    def _parse_virtual_did(self, did: str) -> tuple:
        """解析虚拟设备ID -> (real_did, siid)"""
        try:
            parts = did.split(".")
            real_did = parts[0]
            # .sN 直接对应 siid=N
            # 例如: .s2 -> siid=2, .s3 -> siid=3
            idx = int(parts[1].replace("s", ""))
            siid = idx  # 直接使用 idx，不再 +1
            return real_did, siid
        except:
            return did, 2
            
    def get_device_prop(self, did: str, prop_name: str) -> Any:
        """
        获取设备属性
        """
        if self._is_virtual_did(did):
            return self._get_virtual_prop(did, prop_name)
            
        device = self.get_mijia_device(did)
        if not device:
            return None
        
        try:
            return device.get(prop_name)
        except Exception as e:
            print(f"[MijiaAdapter] 获取属性失败 ({did}.{prop_name}): {e}")
            return None
            
    def _get_virtual_prop(self, did: str, prop_name: str) -> Any:
        """获取虚拟设备属性"""
        # 目前主要支持 switch/light 的 on 属性
        if prop_name not in ["on", "power", "switch-on"]:
            return None
            
        real_did, siid = self._parse_virtual_did(did)
        # 假设开关属性 piid 总是 1
        piid = 1
        
        try:
            result = self._api.get_devices_prop({
                "did": real_did,
                "siid": siid,
                "piid": piid
            })
            return result.get("value")
        except Exception as e:
            print(f"[MijiaAdapter] 获取虚拟属性失败 ({did}): {e}")
            return None
    
    def set_device_prop(self, did: str, prop_name: str, value: Any) -> bool:
        """
        设置设备属性
        """
        # print(f"[MijiaAdapter DEBUG] set_device_prop: did={did}, prop={prop_name}, value={value}")
        
        if self._is_virtual_did(did):
            return self._set_virtual_prop(did, prop_name, value)
            
        device = self.get_mijia_device(did)
        if not device:
            print(f"[MijiaAdapter DEBUG] 无法获取设备实例: {did}")
            return False
        
        try:
            # 检查设备支持的属性列表
            # print(f"[MijiaAdapter DEBUG] 设备支持的属性: {device.prop_list if hasattr(device, 'prop_list') else '未知'}")
            device.set(prop_name, value)
            # print(f"[MijiaAdapter DEBUG] 设置成功: {did}.{prop_name}={value}")
            return True
        except Exception as e:
            print(f"[MijiaAdapter] 设置属性失败 ({did}.{prop_name}={value}): {e}")
            return False
            
    def _set_virtual_prop(self, did: str, prop_name: str, value: Any) -> bool:
        """设置虚拟设备属性"""
        # print(f"[MijiaAdapter DEBUG] _set_virtual_prop: did={did}, prop={prop_name}, value={value}")
        
        # 目前主要支持 switch/light 的 on 属性
        if prop_name not in ["on", "power", "switch-on"]:
            print(f"[MijiaAdapter DEBUG] 不支持的属性: {prop_name}")
            return False
            
        real_did, siid = self._parse_virtual_did(did)
        piid = 1
        
        # 将值转换为布尔类型 (MIoT 协议要求布尔值)
        if isinstance(value, bool):
            bool_value = value
        elif isinstance(value, int):
            bool_value = value != 0
        elif isinstance(value, str):
            bool_value = value.lower() in ["true", "1", "on"]
        else:
            bool_value = bool(value)
        
        # print(f"[MijiaAdapter DEBUG] 解析结果: real_did={real_did}, siid={siid}, piid={piid}, bool_value={bool_value}")
        
        try:
            params = {
                "did": real_did,
                "siid": siid,
                "piid": piid,
                "value": bool_value  # 使用布尔值
            }
            # print(f"[MijiaAdapter DEBUG] 调用 set_devices_prop: {params}")
            result = self._api.set_devices_prop(params)
            # print(f"[MijiaAdapter DEBUG] API 返回结果: {result}")
            code = result.get("code", -1)
            message = result.get("message", "")
            # API 可能返回 code=0 或 code=1 表示成功
            success = code == 0 or (code == 1 and message == "成功")
            # print(f"[MijiaAdapter DEBUG] 控制结果: code={code}, message={message}, success={success}")
            return success
        except Exception as e:
            print(f"[MijiaAdapter] 设置虚拟属性失败 ({did}): {e}")
            return False
    
    def run_device_action(self, did: str, action_name: str, params: Any = None) -> bool:
        """
        执行设备动作
        """
        # 虚拟设备暂不支持复杂动作，除非也是基于 siid 映射
        device = self.get_mijia_device(did)
        if not device:
            return False
        
        try:
            device.run_action(action_name, params)
            return True
        except Exception as e:
            print(f"[MijiaAdapter] 执行动作失败 ({did}.{action_name}): {e}")
            return False
    
    def get_device_status(self, did: str, category: str = "other") -> Dict[str, Any]:
        """
        获取设备状态 (统一接口)
        """
        import time
        
        # 状态缓存 (降低 API 调用频率)
        cache_key = f"status_{did}"
        if hasattr(self, '_status_cache') and cache_key in self._status_cache:
            cached_time, cached_status = self._status_cache[cache_key]
            # 缓存有效期 5 秒
            if time.time() - cached_time < 5:
                return cached_status
        
        # 尝试从缓存获取类别信息
        info = self._device_info_cache.get(did)
        if info:
            category = info.category
            
        if self._is_virtual_did(did):
            result = self._get_virtual_status(did)
            self._cache_status(cache_key, result)
            return result
        
        device = self.get_mijia_device(did)
        if not device:
            return {"online": False}
        
        result = {"online": True}
        
        try:
            # 智能推断开关属性
            power_prop = "on"
            if "on" not in device.prop_list:
                # 尝试查找其他可能的开关属性
                candidates = ["power", "switch", "switch-on", "status", "state"]
                for c in candidates:
                    if c in device.prop_list:
                        power_prop = c
                        break
            
            # 无论是否找到开关属性，设备都在线
            # 不同的设备类别获取不同的额外属性
            
            # 尝试获取电源状态 (如果存在对应的属性)
            if power_prop in device.prop_list:
                try:
                    on_state = device.get(power_prop)
                    # 某些设备返回 None，视为离线或获取失败
                    if on_state is None:
                         # 这里的策略可以调整，如果主要属性都获取不到，可能确实离线
                         pass 
                    else:
                        result["power"] = "on" if on_state else "off"
                except Exception as e:
                    pass
            
            if category == "light":
                try:
                    result["brightness"] = device.get("brightness")
                except:
                    pass
                try:
                    result["color_temperature"] = device.get("color-temperature")
                except:
                    pass
                    
            elif category == "fan":
                try:
                    result["fan_level"] = device.get("fan-level")
                except:
                    pass

            elif category == "purifier":
                # 净化器特有属性
                try:
                    # 尝试获取常用属性，支持短横线和下划线命名
                    result["temperature"] = device.get("temperature")
                    
                    # 湿度
                    hum = device.get("relative-humidity")
                    if hum is None:
                        hum = device.get("relative_humidity")
                    result["humidity"] = hum
                    
                    # PM2.5
                    pm25 = device.get("pm2.5-density")
                    if pm25 is None:
                        pm25 = device.get("pm2.5_density")
                    result["pm25"] = pm25
                    
                    # 空气质量
                    val = device.get("air-quality")
                    if val is None:
                        val = device.get("air_quality")
                    result["air_quality"] = val
                    
                    # 模式
                    result["mode"] = device.get("mode")
                    
                    # 滤芯剩余
                    life = device.get("filter-life-level")
                    if life is None:
                        life = device.get("filter_life_level")
                    result["filter_life"] = life
                    
                except Exception as e:
                    print(f"[MijiaAdapter] 获取净化器属性失败: {e}")
                    pass
            
            # 红外设备特殊处理
            if "ir" in device.model:
                # 红外设备通常无法获取真实状态，默认认为在线
                pass
                    
        except Exception as e:
            print(f"[MijiaAdapter] 获取设备状态失败 ({did}): {e}")
            result["online"] = False
        
        self._cache_status(cache_key, result)
        return result
    
    def _cache_status(self, key: str, status: Dict):
        """缓存设备状态"""
        import time
        if not hasattr(self, '_status_cache'):
            self._status_cache = {}
        self._status_cache[key] = (time.time(), status)

    def _get_virtual_status(self, did: str) -> Dict[str, Any]:
        """获取虚拟设备状态"""
        # 获取 'on' 属性作为状态
        val = self._get_virtual_prop(did, "on")
        if val is not None:
            return {
                "online": True,
                "power": "on" if val else "off"
            }
        return {"online": False}
