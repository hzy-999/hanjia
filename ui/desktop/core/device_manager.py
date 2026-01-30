"""
AquaGuard 小韩智能家庭管理系统 - 设备管理器模块

负责设备的增删改查、状态轮询、客户端工厂
"""

import threading
import time
from typing import List, Optional, Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .device import Device, DeviceType
from .api_client import SensorClient, LightClient
from .mijia_adapter import MijiaAdapter, MijiaDeviceInfo, MIJIA_AVAILABLE
from .notification import NotificationService


class DeviceManager:
    """
    设备管理器
    
    负责管理所有设备的生命周期，包括：
    - 设备的添加/删除/查询
    - 状态轮询
    - 客户端创建
    - 通知推送
    """
    
    def __init__(self, config_manager):
        """
        初始化设备管理器
        
        Args:
            config_manager: ConfigManager 实例，用于持久化设备列表
        """
        self._config = config_manager
        self._devices: Dict[str, Device] = {}
        self._clients: Dict[str, Any] = {}  # 缓存客户端实例
        
        # 轮询相关
        self._polling = False
        self._poll_thread: Optional[threading.Thread] = None
        self._poll_interval_ms = 3000
        self._on_status_update: Optional[Callable[[Device], None]] = None
        
        # 状态追踪 (用于通知)
        self._last_power_state: Dict[str, bool] = {}  # {did: is_on}
        self._notification_service = NotificationService()
        
        # 初始化通知配置
        notify_config = self._config.get_notification_config()
        self._notification_service.set_config(
            token=notify_config.get("token", ""),
            enabled=notify_config.get("enabled", False)
        )
        
        # 米家适配器
        self._mijia_adapter: Optional[MijiaAdapter] = None
        if MIJIA_AVAILABLE:
            auth_path = self._config.get_mijia_auth_path()
            self._mijia_adapter = MijiaAdapter(auth_path)
        
        # 加载设备
        self._load_devices()
        
        # 初始化上一轮状态，避免启动时误报
        # 注意：这里还没有实际状态，需要等第一次轮询后填充
        self._initial_poll_done = False
    
    def _load_devices(self) -> None:
        """从配置加载设备列表"""
        devices_data = self._config.get_devices()
        for d in devices_data:
            device = Device.from_dict(d)
            self._devices[device.id] = device
            print(f"[设备管理] 已加载设备: {device.name} ({device.ip})")
    
    
    def save_devices(self) -> None:
        """保存设备列表到配置"""
        devices_list = [d.to_dict() for d in self._devices.values()]
        self._config.set_devices(devices_list)
        self._config.save()
        
    def _save_devices(self) -> None:
        """保存设备列表到配置 (Internal alias)"""
        self.save_devices()

    
    # ============ 设备 CRUD ============
    
    def add_device(self, name: str, device_type: DeviceType, ip: str) -> Device:
        """
        添加新设备
        
        Args:
            name: 设备名称
            device_type: 设备类型
            ip: IP 地址
            
        Returns:
            新创建的 Device 实例
        """
        device = Device(name=name, type=device_type, ip=ip)
        self._devices[device.id] = device
        self._save_devices()
        print(f"[设备管理] 已添加设备: {device.name} ({device.ip})")
        return device
    
    def remove_device(self, device_id: str) -> bool:
        """
        删除设备
        
        Args:
            device_id: 设备 ID
            
        Returns:
            是否删除成功
        """
        if device_id in self._devices:
            device = self._devices.pop(device_id)
            # 清理客户端缓存
            if device_id in self._clients:
                del self._clients[device_id]
            self._save_devices()
            print(f"[设备管理] 已删除设备: {device.name}")
            return True
        return False
    
    def update_device(self, device_id: str, name: str = None, ip: str = None) -> bool:
        """
        更新设备信息
        
        Args:
            device_id: 设备 ID
            name: 新名称 (可选)
            ip: 新 IP (可选)
            
        Returns:
            是否更新成功
        """
        if device_id not in self._devices:
            return False
        
        device = self._devices[device_id]
        if name is not None:
            device.name = name
        if ip is not None:
            device.ip = ip
            # IP 变化需要清除客户端缓存
            if device_id in self._clients:
                del self._clients[device_id]
        
        self._save_devices()
        return True
    
    def get_device(self, device_id: str) -> Optional[Device]:
        """获取指定设备"""
        return self._devices.get(device_id)
    
    def get_all_devices(self) -> List[Device]:
        """获取所有设备列表"""
        return list(self._devices.values())
    
    def get_devices_by_type(self, device_type: DeviceType) -> List[Device]:
        """按类型获取设备列表"""
        return [d for d in self._devices.values() if d.type == device_type]
    
    def get_mijia_devices(self) -> List[Device]:
        """获取所有米家设备"""
        return [d for d in self._devices.values() if d.is_mijia]
    
    # ============ 米家设备管理 ============
    
    @property
    def mijia_adapter(self) -> Optional[MijiaAdapter]:
        """获取米家适配器"""
        return self._mijia_adapter
    
    def is_mijia_available(self) -> bool:
        """米家功能是否可用"""
        return MIJIA_AVAILABLE and self._mijia_adapter is not None
    
    def is_mijia_logged_in(self) -> bool:
        """米家是否已登录"""
        if self._mijia_adapter:
            return self._mijia_adapter.is_logged_in
        return False
    
    def add_mijia_device(self, info: MijiaDeviceInfo) -> Device:
        """
        添加米家设备
        
        Args:
            info: 米家设备信息
            
        Returns:
            新创建的 Device 实例
        """
        # 根据类别确定设备类型
        category_to_type = {
            "light": DeviceType.MIJIA_LIGHT,
            "switch": DeviceType.MIJIA_SWITCH,
            "fan": DeviceType.MIJIA_FAN,
            "sensor": DeviceType.MIJIA_SENSOR,
        }
        device_type = category_to_type.get(info.category, DeviceType.MIJIA)
        
        device = Device(
            name=info.name,
            type=device_type,
            did=info.did,
            model=info.model
        )
        self._devices[device.id] = device
        self._save_devices()
        print(f"[设备管理] 已添加米家设备: {device.name} (did={info.did})")
        return device
    
    def sync_mijia_devices(self) -> int:
        """
        同步米家设备列表
        
        从米家账户获取设备列表，添加未存在的设备
        
        Returns:
            新添加的设备数量
        """
        if not self.is_mijia_logged_in():
            return 0
        
        # 获取米家设备列表
        mijia_devices = self._mijia_adapter.get_devices()
        
        # 获取已存在的 did 集合
        existing_dids = {d.did for d in self._devices.values() if d.did}
        
        added_count = 0
        for info in mijia_devices:
            if info.did not in existing_dids:
                self.add_mijia_device(info)
                added_count += 1
        
        print(f"[设备管理] 米家设备同步完成，新增 {added_count} 台设备")
        return added_count
    
    # ============ 客户端工厂 ============
    
    def get_client(self, device: Device):
        """
        获取设备对应的客户端实例 (工厂模式)
        
        Args:
            device: 设备实例
            
        Returns:
            SensorClient、LightClient 或 mijiaDevice 实例
        """
        if device.id in self._clients:
            return self._clients[device.id]
        
        # ESP 灯光设备
        if device.type == DeviceType.LIGHT:
            client = LightClient(device.ip)
        # ESP 传感器设备
        elif device.type == DeviceType.SENSOR:
            client = SensorClient(device.ip)
        # 米家设备
        elif device.is_mijia and self._mijia_adapter and device.did:
            client = self._mijia_adapter.get_mijia_device(device.did)
        else:
            # 默认返回 None，未知类型
            return None
        
        if client:
            self._clients[device.id] = client
        return client
    
    # ============ 状态轮询 ============
    
    def set_poll_interval(self, interval_ms: int) -> None:
        """设置轮询间隔"""
        self._poll_interval_ms = max(1000, interval_ms)
    
    def set_status_callback(self, callback: Callable[[Device], None]) -> None:
        """
        设置状态更新回调
        
        Args:
            callback: 回调函数，参数为更新后的 Device
        """
        self._on_status_update = callback
    
    def start_polling(self) -> None:
        """启动状态轮询"""
        if self._polling:
            return
        
        self._polling = True
        self._first_poll_done = False  # 标记首次轮询是否完成
        self._poll_start_time = time.time()  # 记录启动时间
        print(f"[设备管理] 状态轮询已启动 (T+0.0s)")
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
    
    def stop_polling(self) -> None:
        """停止状态轮询"""
        self._polling = False
        if self._poll_thread:
            self._poll_thread.join(timeout=2.0)
            self._poll_thread = None
        print("[设备管理] 状态轮询已停止")
    
    def _poll_loop(self) -> None:
        """轮询循环"""
        # 启动时立即执行一次轮询，不等待
        elapsed = time.time() - self._poll_start_time
        print(f"[设备管理] 开始首次轮询 (T+{elapsed:.1f}s)")
        self._poll_all_devices()
        elapsed = time.time() - self._poll_start_time
        print(f"[设备管理] 首次轮询完成 (T+{elapsed:.1f}s)")
        self._first_poll_done = True
        
        while self._polling:
            time.sleep(self._poll_interval_ms / 1000.0)
            if self._polling:  # 检查是否仍在运行
                self._poll_all_devices()
    
    def _poll_all_devices(self) -> None:
        """并发轮询所有设备"""
        devices = list(self._devices.values())
        if not devices:
            return
            
        # 1. 快速批量更新米家设备在线状态
        if self.is_mijia_logged_in():
            try:
                # 这一步很快，一次请求获取所有设备在线状态
                ts = time.time()
                mijia_list = self._mijia_adapter.get_devices()
                te = time.time()
                print(f"[设备管理] get_devices() 耗时: {te-ts:.3f}s")
                mijia_list = mijia_list or [] # 防止 None
                mijia_status_map = {d.did: d.is_online for d in mijia_list}
                
                # 更新本地状态
                for d in devices:
                    if d.did and d.did in mijia_status_map:
                        d.online = mijia_status_map[d.did]
                        # 如果是在线状态且没有 power 属性，可以先标记为在线
                        if d.online and "power" not in d.data:
                             # 触发一次简单回调，让 UI 显示在线（即使还没获取到详细属性）
                             # 仅当设备可见时才触发回调
                             if self._on_status_update and d.visible:
                                 self._on_status_update(d)
                
                # 初始化状态监控 (仅一次)
                if not self._initial_poll_done:
                    # 记录初始状态，避免启动时误报
                    for d in devices:
                        is_on = d.data.get("is_on", False)
                        self._last_power_state[d.id] = is_on
                    self._initial_poll_done = True
                else:
                    # 检查状态变化并通知
                    self._check_power_change_and_notify(devices)


            except Exception as e:
                print(f"[设备管理] 批量获取在线状态失败: {e}")

        # 2. 筛选需要详细轮询的设备
        # - ESP 设备 (无 DID)
        # - 可见且在线的米家设备 (visible=True, online=True)
        # - 从未获取过数据的可见米家设备
        targets = []
        for d in devices:
            if not d.visible:
                continue
                
            if not d.did: # ESP 设备
                targets.append(d)
            elif d.online: # 在线的米家设备
                targets.append(d)
            elif not d.last_seen: # 从未见过的设备
                targets.append(d)
        
        if not targets:
            return
            
        # 使用更大的线程池以加快并发获取（米家 API 较慢，需要更多并发）
        max_workers = min(20, len(targets))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self._poll_device, d): d for d in targets}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"[设备管理] 轮询出错: {e}")
    
    def _poll_device(self, device: Device) -> None:
        """
        轮询单个设备
        
        Args:
            device: 设备实例
        """
        # 米家设备使用专门的轮询方法
        if device.is_mijia:
            self._poll_mijia_device(device)
            return
        
        # ESP 设备使用 HTTP 客户端
        client = self.get_client(device)
        if client is None:
            return
        
        try:
            status = client.get_status()
            if status:
                device.mark_online()
                # 更新设备数据
                if device.type == DeviceType.LIGHT:
                    device.data = {
                        "power": status.power,
                        "mode": status.mode,
                        "color_r": status.color_r,
                        "color_g": status.color_g,
                        "color_b": status.color_b,
                        "wifi_signal": status.wifi_signal
                    }
                elif device.type == DeviceType.SENSOR:
                    device.data = {
                        "temperature": status.temperature,
                        "tds_value": status.tds_value,
                        "water_level": status.water_level,
                        "wifi_signal": status.wifi_signal
                    }
            else:
                device.mark_failed()
        except Exception as e:
            device.mark_failed()
            print(f"[设备管理] 轮询 {device.name} 失败: {e}")
        
        # 触发回调
        if self._on_status_update:
            try:
                self._on_status_update(device)
            except Exception as e:
                print(f"[设备管理] 状态回调出错: {e}")

    def _check_power_change_and_notify(self, devices: List[Device]) -> None:
        """检查设备开关状态变化并发送通知"""
        # 获取基础配置
        notify_config = self._config.get_notification_config()
        # print(f"[DEBUG] Check notify: enabled={notify_config.get('enabled')}") 
        
        if not notify_config.get("enabled"):
            return
            
        # 获取规则配置
        rules = self._config.get_notification_rules()
        # print(f"[DEBUG] Rules: {rules}")

        for d in devices:
            if not d.visible:
                continue
                
            # 获取当前开关状态
            # 兼容 is_on (bool) 和 power (str)
            current_is_on = d.data.get("is_on")
            if current_is_on is None:
                current_is_on = (d.data.get("power") == "on")
                
            last_is_on = self._last_power_state.get(d.id)
            
            # 如果是首次记录，直接保存并不通知
            if last_is_on is None:
                self._last_power_state[d.id] = current_is_on
                continue

            # 如果状态发生变化
            if current_is_on != last_is_on:
                # 更新记录
                self._last_power_state[d.id] = current_is_on
                
                # 状态描述
                action = "开启" if current_is_on else "关闭"
                action_key = "on" if current_is_on else "off"
                
                # ===== 记录状态变更日志（记录所有设备变更，不论是否推送）=====
                if self._config.is_status_log_enabled():
                    import uuid
                    log_entry = {
                        "id": str(uuid.uuid4()),
                        "device_id": d.id,
                        "device_name": d.name,
                        "action": action,
                        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                        "read": False
                    }
                    self._config.add_status_log(log_entry)
                    print(f"[状态记录] 已记录: {d.name} -> {action}")
                
                # ===== 检查是否需要推送通知 =====
                # 只有明确配置了规则并且该动作设为 True 的设备才推送
                # 没有配置规则的设备默认不推送
                device_rule = rules.get(d.id)
                
                # 默认不推送，除非明确配置了该动作为 True
                should_notify = False
                if device_rule:
                    should_notify = device_rule.get(action_key, False)
                
                if not should_notify:
                   print(f"[DEBUG] 忽略推送: {d.name} -> {action_key} (未启用该设备推送)")
                   continue

                # 准备通知内容
                title = f"请注意,{d.name}已{action}!"
                content = ""  # 内容留空,主要信息在标题中
                
                print(f"[通知] 检测到状态变化: {d.name} -> {action}, 准备发送推送...")
                
                # 发送通知
                success = self._notification_service.send_push(title, content)
                print(f"[通知] 推送请求已提交")
    
    def _poll_mijia_device(self, device: Device) -> None:
        """
        轮询米家设备
        
        Args:
            device: 设备实例
        """
        if not self._mijia_adapter:
            print(f"[设备管理] 米家设备 {device.name}: adapter 不可用")
            device.mark_failed()
            return
        
        if not device.did:
            print(f"[设备管理] 米家设备 {device.name}: 缺少 did")
            device.mark_failed()
            return
        
        if not self._mijia_adapter.is_logged_in:
            # 静默失败，不输出日志（避免刷屏）
            device.mark_failed()
            return
        
        try:
            # 从设备类型推断类别
            category_map = {
                DeviceType.MIJIA_LIGHT: "light",
                DeviceType.MIJIA_SWITCH: "switch",
                DeviceType.MIJIA_FAN: "fan",
                DeviceType.MIJIA_SENSOR: "sensor",
            }
            category = category_map.get(device.type, "other")
            
            status = self._mijia_adapter.get_device_status(device.did, category)
            if status.get("online", False):
                device.mark_online()
                device.data = status
            else:
                device.mark_failed()
        except Exception as e:
            device.mark_failed()
            print(f"[设备管理] 轮询米家设备 {device.name} 失败: {e}")
        
        # 触发回调
        if self._on_status_update:
            try:
                self._on_status_update(device)
            except Exception as e:
                print(f"[设备管理] 状态回调出错: {e}")
    
    def poll_device_now(self, device_id: str) -> Optional[Device]:
        """
        立即轮询指定设备 (同步)
        
        Args:
            device_id: 设备 ID
            
        Returns:
            更新后的设备实例
        """
        device = self.get_device(device_id)
        if device:
            self._poll_device(device)
            return device
        return None
    
    def control_mijia_device(self, device_id: str, action: str, params: Dict[str, Any]) -> bool:
        """
        控制米家设备
        
        Args:
            device_id: 设备 ID
            action: 动作名称 (set_power, set_mode, etc.)
            params: 参数字典
            
        Returns:
            是否成功
        """
        print(f"[DeviceManager DEBUG] control_mijia_device: device_id={device_id}, action={action}")
        
        device = self.get_device(device_id)
        if not device:
            print(f"[DeviceManager DEBUG] 设备不存在: {device_id}")
            return False
            
        print(f"[DeviceManager DEBUG] 设备信息: name={device.name}, is_mijia={device.is_mijia}, did={device.did}")
        
        if not device.is_mijia:
            print(f"[DeviceManager DEBUG] 设备不是米家设备")
            return False
            
        if not self._mijia_adapter:
            print(f"[DeviceManager DEBUG] 米家适配器未初始化")
            return False
            
        if action == "set_power":
            power_on = params.get("power", False)
            print(f"[DeviceManager DEBUG] 调用 set_device_prop: did={device.did}, on={power_on}")
            # 尝试设置 'on' 属性 (大多数设备使用这个)
            return self._mijia_adapter.set_device_prop(device.did, "on", power_on)
            
        return False
