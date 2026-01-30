"""
AquaGuard 韩家家庭智能系统 - 主应用窗口 (V2 多设备版)

赛博朋克暗色主题的桌面应用程序
支持多设备管理和实时状态显示
"""

import customtkinter as ctk
from typing import Optional
import threading
import winsound

from .dashboard import DashboardPanel
from .lighting import LightingPanel
from .automation import AutomationPanel
from .device_grid import DeviceGridPanel
from .add_device_dialog import AddDeviceDialog, EditDeviceDialog
from .mijia_login_dialog import MijiaLoginDialog
from .mijia_device_panel import MijiaDevicePanel
from .multi_switch_detail import MultiSwitchDetailPanel
from .theme import Theme  # 引入主题
from .settings_panel import SettingsPanel # 引入新版设置面板

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import ConfigManager, get_config
from core.api_client import SensorClient, LightClient
from core.scheduler import Scheduler, AlertManager
from core.device import Device, DeviceType
from core.device_manager import DeviceManager


class AquaGuardApp(ctk.CTk):
    """AquaGuard 主应用 (V2 多设备版)"""
    
    def __init__(self):
        super().__init__()
        
        # 设置主题
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # 窗口配置
        self.title("🐠 AquaGuard 韩家家庭智能系统")
        self.geometry("1200x700")
        self.minsize(1000, 600)
        
        # 设置窗口背景色
        self.configure(fg_color=Theme.BG_PRIMARY)
        
        # 加载配置
        self.config = get_config()
        
        # 初始化设备管理器
        self.device_manager = DeviceManager(self.config)
        
        # 保留旧的客户端用于兼容 (定时任务等)
        self.sensor_client = SensorClient(self.config.get_sensor_ip())
        self.light_client = LightClient(self.config.get_light_ip())
        
        # 初始化调度器和报警管理器
        self.scheduler = Scheduler()
        self.alert_manager = AlertManager()
        
        # 当前页面和选中的设备
        self._current_page = "devices"
        self._selected_device_id: Optional[str] = None
        
        # 设备在线状态缓存 (用于检测状态变化)
        self._device_online_cache = {}
        
        # 创建 UI
        self._create_ui()
        
        # 启动设备轮询
        self._start_device_polling()
        
        # 延迟刷新设备网格 (等待首次轮询完成后刷新)
        self.after(2000, self._refresh_device_grid)  # 2秒后刷新
        
        # 启动调度器
        self._start_scheduler()
        
        # 绑定关闭事件
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_ui(self) -> None:
        """创建 UI"""
        # 主容器
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 左侧导航栏 (Modern White Sidebar)
        self.nav_frame = ctk.CTkFrame(
            self.main_container,
            width=220,  # 稍微加宽
            fg_color=Theme.BG_CARD,
            corner_radius=0 # 侧边栏垂直铺满，不需要圆角
        )
        self.nav_frame.pack(side="left", fill="y")
        self.nav_frame.pack_propagate(False)
        
        # Logo
        logo_label = ctk.CTkLabel(
            self.nav_frame,
            text="🐠 AquaGuard",
            font=(Theme.FONT_FAMILY, 18, "bold"),
            text_color=Theme.ACCENT_PRIMARY
        )
        logo_label.pack(pady=(20, 5))
        
        version_label = ctk.CTkLabel(
            self.nav_frame,
            text="v2.0.1 Theme Update",
            font=(Theme.FONT_FAMILY, 10),
            text_color=Theme.TEXT_MUTED
        )
        version_label.pack(pady=(0, 20))
        
        # 导航按钮
        self.nav_buttons = {}
        
        nav_items = [
            ("devices", "📱  我的设备"),
            ("automation", "🤖  鱼缸信息"),
            ("settings", "⚙️  系统设置")
        ]
        
        for page_id, text in nav_items:
            btn = ctk.CTkButton(
                self.nav_frame,
                text=text,
                font=(Theme.FONT_FAMILY, 15),
                fg_color="transparent",
                text_color=Theme.TEXT_SECONDARY,
                hover_color=Theme.BG_SECONDARY, # 使用 Slate 100，更好的灰度视觉反馈
                anchor="w",
                height=45,
                corner_radius=8,
                command=lambda p=page_id: self._switch_page(p)
            )
            btn.pack(fill="x", padx=15, pady=5)
            self.nav_buttons[page_id] = btn
        
        # 返回按钮
        self.back_btn = ctk.CTkButton(
            self.nav_frame,
            text="←  返回设备列表",
            font=(Theme.FONT_FAMILY, 14),
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BG_SECONDARY, # 视觉更清晰
            text_color=Theme.ACCENT_PRIMARY,
            height=40,
            command=self._back_to_devices
        )
        # 初始隐藏
        
        # 右侧内容区 (Soft Basin)
        self.content_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CORNER_RADIUS  # 使用主题大圆角
        )
        self.content_frame.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=0)
        
        # 创建页面
        self.pages = {}
        self._detail_page_cache = {}  # device_id -> (wrapper, panel)
        
        # 设备网格页面
        self.pages["devices"] = DeviceGridPanel(
            self.content_frame,
            on_device_click=self._on_device_click,
            on_device_menu=self._on_device_menu,
            on_add_device=self._on_add_device,
            on_notification_click=self._on_notification_click
        )
        
        # 鱼缸信息页面
        self.pages["automation"] = AutomationPanel(
            self.content_frame,
            on_alert_settings_change=self._on_alert_settings_change,
            on_schedule_change=self._on_schedule_change
        )

        # 设置页面 (新版)
        self.pages["settings"] = SettingsPanel(
            self.content_frame,
            config=self.config,
            device_manager=self.device_manager,
            config_manager=self.config, # ConfigManager 实例需传递
            on_save=self._on_settings_save
        )
        # 设置回调
        self.pages["settings"].set_callbacks(
            on_bind=self._on_mijia_bind,
            on_unbind=self._on_mijia_unbind,
            on_sync=self._on_mijia_sync,
            on_vis_change=self._on_visibility_change_simple, # 需要适配方法签名
            on_vis_refresh=self._on_visibility_refresh
        )
        
        # 设备详情页 (动态创建)
        self.pages["device_detail"] = None
        
        # 通知面板引用
        self._notification_panel = None
        
        # 刷新设备列表
        self._refresh_device_grid()
        
        # 初始化未读消息数量
        self._update_unread_count()
        
        # 显示默认页面
        self._switch_page("devices")
    
    def _refresh_device_grid(self) -> None:
        """刷新设备网格 (异步入口)"""
        # 启动后台线程准备数据，避免阻塞 UI
        threading.Thread(target=self._refresh_device_grid_async, daemon=True).start()

    def _refresh_device_grid_async(self) -> None:
        """后台线程：准备设备数据"""
        import time
        t_start = time.time()
        try:
            all_devices = self.device_manager.get_all_devices()
            # 过滤：只显示 visible=True 的设备
            devices = [d for d in all_devices if d.visible]
            # 排序：在线设备优先 (online=True 对应 0, False 对应 1), 然后按名称排序
            devices.sort(key=lambda x: (not x.online, x.name))
            
            device_data = []
            # update cache
            self._device_online_cache = {}
            
            for d in devices:
                self._device_online_cache[d.id] = d.online
                
                is_on = False
                # ESP 灯光设备
                if d.online and d.type == DeviceType.LIGHT:
                    if d.data.get("power") == "on":
                        is_on = True
                # 米家灯光/开关/风扇设备
                elif d.online and d.type in (DeviceType.MIJIA_LIGHT, DeviceType.MIJIA_SWITCH, DeviceType.MIJIA_FAN):
                    if d.data.get("power") == "on":
                        is_on = True
                
                # 准备传给 UI 的纯数据字典
                device_data.append({
                    "id": d.id,
                    "did": d.did,
                    "name": d.name,
                    "icon": d.icon,
                    "color": d.color,
                    "online": d.online,
                    "is_on": is_on,
                    "status_text": d.get_status_text()
                })
            
            t_data = time.time()
            print(f"[性能监控] 数据准备耗时: {(t_data - t_start)*1000:.1f}ms (设备数: {len(devices)})")
            
            # 数据准备完毕，调度主线程更新 UI
            self.after(0, lambda: self._update_device_grid_ui(device_data))
            
        except Exception as e:
            print(f"[UI] 异步刷新数据出错: {e}")

    def _update_device_grid_ui(self, device_data: list) -> None:
        """主线程：更新 UI 组件"""
        import time
        t_ui_start = time.time()
        
        # 再次检查页面是否存在，防止关闭时报错
        if "devices" in self.pages:
            self.pages["devices"].set_devices(device_data, on_switch_click=self._on_multi_switch_click)
            
        t_ui_end = time.time()
        print(f"[性能监控] UI渲染耗时: {(t_ui_end - t_ui_start)*1000:.1f}ms")

    def _switch_page(self, page_id: str) -> None:
        """切换页面"""
        # 隐藏所有页面
        for page in self.pages.values():
            if page:
                page.pack_forget()
        
        # 隐藏返回按钮
        self.back_btn.pack_forget()
        
        # 显示目标页面
        if page_id in self.pages and self.pages[page_id]:
            self.pages[page_id].pack(fill="both", expand=True, padx=20, pady=20)
            self._current_page = page_id
        
        # 更新导航按钮样式
        for nav_id, btn in self.nav_buttons.items():
            if nav_id == page_id:
                btn.configure(
                    fg_color=Theme.ACCENT_PRIMARY, 
                    text_color="#FFFFFF",
                    hover_color=Theme.ACCENT_HOVER  # 选中时悬停也保持深色
                )
            else:
                btn.configure(
                    fg_color="transparent", 
                    text_color=Theme.TEXT_SECONDARY,
                    hover_color=Theme.BG_SECONDARY
                )

    def _back_to_devices(self) -> None:
        """返回设备列表"""
        self._selected_device_id = None
        self._current_detail_panel = None  # 清除详情面板引用
        self._refresh_device_grid()
        self._switch_page("devices")

    def _on_settings_save(self) -> None:
        """设置保存后的回调"""
        # 更新调度器
        self.scheduler.set_refresh_interval(self.config.get_refresh_interval())
        self.device_manager.set_poll_interval(self.config.get_refresh_interval())
        # 刷新设备网格（确保米家设备同步后显示）
        self._refresh_device_grid()
        # 更新未读数量
        self._update_unread_count()

    # ============ 状态变更记录相关 ============
    
    def _update_unread_count(self) -> None:
        """更新未读消息数量"""
        count = self.config.get_unread_count()
        self.pages["devices"].update_unread_count(count)
    
    def _on_notification_click(self) -> None:
        """通知按钮点击 - 打开消息记录面板"""
        from .notification_log_panel import NotificationLogPanel
        
        # 如果已经打开则返回
        if self._notification_panel and self._notification_panel.winfo_exists():
            self._notification_panel.focus()
            return
        
        # 获取消息记录
        logs = self.config.get_status_logs()
        
        # 创建面板
        self._notification_panel = NotificationLogPanel(
            self,
            logs=logs,
            on_mark_read=self._on_log_mark_read,
            on_mark_all_read=self._on_log_mark_all_read,
            on_clear=self._on_log_clear,
            on_close=self._on_notification_panel_close
        )
    
    def _on_log_mark_read(self, log_id: str) -> None:
        """标记单条已读"""
        self.config.mark_log_read(log_id)
        self._update_unread_count()
    
    def _on_log_mark_all_read(self) -> None:
        """标记全部已读"""
        self.config.mark_all_logs_read()
        self._update_unread_count()
    
    def _on_log_clear(self) -> None:
        """清空记录"""
        self.config.clear_status_logs()
        self._update_unread_count()
    
    def _on_notification_panel_close(self) -> None:
        """通知面板关闭"""
        self._notification_panel = None
        self._update_unread_count()

    # ============ 设备管理回调 ============

    def _on_device_click(self, device_id: str) -> None:
        """设备点击 - 进入详情页"""
        device = self.device_manager.get_device(device_id)
        if not device:
            return
        
        self._selected_device_id = device_id
        
        # 隐藏当前页面
        for page in self.pages.values():
            if page:
                page.pack_forget()
                
        # 隐藏所有已缓存的详情页 (确保没有重叠)
        for wrapper, _ in self._detail_page_cache.values():
            wrapper.pack_forget()
            
        # 检查缓存
        if device_id in self._detail_page_cache:
            wrapper, panel = self._detail_page_cache[device_id]
            wrapper.pack(fill="both", expand=True)
            self.pages["device_detail"] = wrapper
            self._current_detail_panel = panel
            
            # 立即触发一次状态更新
            self._update_detail_panel(device)
            return

        # 创建详情页包装容器（包含返回按钮和实际详情面板）
        detail_wrapper = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        detail_wrapper.pack(fill="both", expand=True) # 立即显示
        
        # 顶部导航栏
        nav_frame = ctk.CTkFrame(detail_wrapper, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # 返回按钮
        back_btn = ctk.CTkButton(
            nav_frame,
            text="← 返回",
            width=80,
            height=32,
            fg_color="transparent",
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            font=(Theme.FONT_FAMILY, 13),
            command=self._back_to_devices
        )
        back_btn.pack(side="left")
        
        # 标题
        title_label = ctk.CTkLabel(
            nav_frame,
            text=device.name,
            font=(Theme.FONT_FAMILY, 20, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title_label.pack(side="left", padx=20)
        
        # 在线状态
        status_text = "在线" if device.online else "离线"
        status_color = Theme.ACCENT_PRIMARY if device.online else Theme.TEXT_MUTED
        status_label = ctk.CTkLabel(
            nav_frame,
            text=status_text,
            font=(Theme.FONT_FAMILY, 12),
            text_color=status_color
        )
        status_label.pack(side="right")
        
        # 分隔线
        separator = ctk.CTkFrame(detail_wrapper, fg_color=Theme.BORDER_DEFAULT, height=1)
        separator.pack(fill="x", padx=20, pady=10)
        
        # 详情内容容器
        content_container = ctk.CTkFrame(detail_wrapper, fg_color="transparent")
        content_container.pack(fill="both", expand=True)
        
        # 根据设备类型创建详情页
        if device.type == DeviceType.LIGHT:
            # 创建灯控制面板 (ESP)
            detail_panel = LightingPanel(
                content_container,
                on_power_change=lambda on: self._on_light_power_change_for_device(device_id, on),
                on_color_change=lambda r, g, b: self._on_light_color_change_for_device(device_id, r, g, b),
                on_mode_change=lambda m: self._on_light_mode_change_for_device(device_id, m)
            )
            
            # 更新状态
            if device.online and device.data:
                detail_panel.update_light_status(
                    power=device.data.get("power", "off"),
                    mode=device.data.get("mode", "static"),
                    r=device.data.get("color_r", 255),
                    g=device.data.get("color_g", 255),
                    b=device.data.get("color_b", 255),
                    connected=True
                )
            else:
                detail_panel.set_disconnected()
                
        elif device.type == DeviceType.SENSOR:
            # 创建传感器仪表盘 (ESP)
            detail_panel = DashboardPanel(content_container)
            
            if device.online and device.data:
                detail_panel.update_sensor_data(
                    temperature=device.data.get("temperature", 0),
                    tds=device.data.get("tds_value", 0),
                    water_level=device.data.get("water_level", 1),
                    connected=True,
                    wifi_signal=device.data.get("wifi_signal", 0)
                )
                
                # 检查报警
                self.alert_manager.check(
                    device.data.get("temperature", 0),
                    device.data.get("tds_value", 0),
                    device.data.get("water_level", 1)
                )
            else:
                detail_panel.set_disconnected()
                
        # 处理所有米家设备类型
        elif device.is_mijia:
            detail_panel = MijiaDevicePanel(
                content_container,
                device_name=device.name,
                device_model=device.model,
                on_power_change=lambda on: self._on_mijia_power_change(device_id, on)
            )
            
            if device.online and device.data:
                detail_panel.update_status(True, device.data)
            else:
                detail_panel.update_status(False, {})
                
        else:
            detail_wrapper.destroy()
            return
        
        detail_panel.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 存入缓存
        self._detail_page_cache[device_id] = (detail_wrapper, detail_panel)
        
        self.pages["device_detail"] = detail_wrapper
        self._current_detail_panel = detail_panel  # 保存实际面板引用
        detail_wrapper.pack(fill="both", expand=True)
        
        # 更新导航按钮样式
        for nav_id, btn in self.nav_buttons.items():
            btn.configure(fg_color="transparent", text_color=Theme.TEXT_SECONDARY)

    def _on_mijia_power_change(self, device_id: str, power_on: bool) -> None:
        """米家设备开关控制"""
        device = self.device_manager.get_device(device_id)
        if not device or not device.is_mijia:
            return

        def do_action():
            success = self.device_manager.control_mijia_device(
                device_id, 
                "set_power", 
                {"power": power_on}
            )
            
            def update_ui():
                if success:
                    # 更新本地状态
                    device.data["power"] = "on" if power_on else "off"
                    # 刷新界面
                    self._update_device_ui(device)
                    print(f"[App] 米家设备 {device.name} 开关: {'开' if power_on else '关'}")
                else:
                    print(f"[App] 米家设备控制失败: {device.name}")
                    # 恢复开关状态 (需要在主线程执行)
                    self._update_device_ui(device)
            
            # 回到主线程更新 UI
            self.after(0, update_ui)
            
        threading.Thread(target=do_action, daemon=True).start()
    
    def _on_multi_switch_click(self, device_id: str, switches: list) -> None:
        """多键开关卡片点击 - 进入详情页"""
        print(f"[App] 点击多键开关: {device_id}, 开关数: {len(switches)}")
        
        # 隐藏设备列表页
        self.pages["devices"].pack_forget()
        
        # 获取第一个子开关的在线状态
        is_online = False
        if switches:
            first_switch_id = switches[0].get("id")
            if first_switch_id:
                device = self.device_manager.get_device(first_switch_id)
                if device:
                    is_online = device.online
        
        # 确定设备名称
        if len(switches) == 3:
            device_name = "三键开关"
        elif len(switches) == 2:
            device_name = "双键开关"
        else:
            device_name = f"{len(switches)}键开关"
        
        # 创建详情页
        self._current_multi_switch_detail = MultiSwitchDetailPanel(
            self.content_frame,
            device_name=device_name,
            switches=switches,
            is_online=is_online,
            on_switch_change=self._on_multi_switch_change,
            on_back=self._back_from_multi_switch
        )
        self._current_multi_switch_detail.pack(fill="both", expand=True)
        self._current_multi_switch_id = device_id
        self._current_multi_switches = switches
    
    def _on_multi_switch_change(self, switch_id: str, new_state: bool) -> None:
        """多键开关详情页中的开关控制"""
        device = self.device_manager.get_device(switch_id)
        if not device or not device.is_mijia:
            print(f"[App] 多键开关设备未找到: {switch_id}")
            return
        
        def do_action():
            success = self.device_manager.control_mijia_device(
                switch_id,
                "set_power",
                {"power": new_state}
            )
            
            def update_ui():
                if success:
                    device.data["power"] = "on" if new_state else "off"
                    # 更新详情页中的开关状态
                    if hasattr(self, '_current_multi_switch_detail') and self._current_multi_switch_detail:
                        self._current_multi_switch_detail.update_switch_state(switch_id, new_state)
                    # 更新首页卡片状态
                    self.pages["devices"].update_switch_state(switch_id, new_state)
                    print(f"[App] 多键开关 {device.name} 开关: {'开' if new_state else '关'}")
                else:
                    print(f"[App] 多键开关控制失败: {device.name}")
                    # 恢复开关状态
                    if hasattr(self, '_current_multi_switch_detail') and self._current_multi_switch_detail:
                        self._current_multi_switch_detail.update_switch_state(switch_id, not new_state)
            
            self.after(0, update_ui)
        
        threading.Thread(target=do_action, daemon=True).start()
    
    def _back_from_multi_switch(self) -> None:
        """从多键开关详情页返回"""
        if hasattr(self, '_current_multi_switch_detail') and self._current_multi_switch_detail:
            self._current_multi_switch_detail.destroy()
            self._current_multi_switch_detail = None
        
        # 刷新并显示设备列表
        self._refresh_device_grid()
        self.pages["devices"].pack(fill="both", expand=True)

    def _on_device_menu(self, device_id: str) -> None:
        """设备右键菜单 - 编辑/删除"""
        device = self.device_manager.get_device(device_id)
        if not device:
            return
        
        dialog = EditDeviceDialog(
            self,
            device_id=device_id,
            device_name=device.name,
            device_ip=device.ip,
            on_save=self._on_device_edit_save,
            on_delete=self._on_device_delete
        )
        dialog.focus()

    def _on_add_device(self) -> None:
        """添加设备"""
        dialog = AddDeviceDialog(
            self,
            on_save=self._on_device_add_save
        )
        dialog.focus()

    def _on_device_add_save(self, name: str, device_type: str, ip: str) -> None:
        """添加设备保存回调"""
        dtype = DeviceType(device_type)
        self.device_manager.add_device(name, dtype, ip)
        self._refresh_device_grid()

    def _on_device_edit_save(self, device_id: str, name: str, ip: str) -> None:
        """编辑设备保存回调"""
        self.device_manager.update_device(device_id, name=name, ip=ip)
        self._refresh_device_grid()

    def _on_device_delete(self, device_id: str) -> None:
        """删除设备回调"""
        self.device_manager.remove_device(device_id)
        self._refresh_device_grid()

    # ============ 设备轮询 ============

    def _start_device_polling(self) -> None:
        """启动设备状态轮询"""
        self.device_manager.set_poll_interval(self.config.get_refresh_interval())
        self.device_manager.set_status_callback(self._on_device_status_update)
        self.device_manager.start_polling()


    def _on_device_status_update(self, device: Device) -> None:
        """设备状态更新回调"""
        # 记录首次收到设备状态的时间
        if not hasattr(self, '_first_status_received'):
            self._first_status_received = set()
        
        if device.id not in self._first_status_received:
            self._first_status_received.add(device.id)
            import time
            if hasattr(self.device_manager, '_poll_start_time'):
                elapsed = time.time() - self.device_manager._poll_start_time
                print(f"[App] 首次收到设备状态: {device.name} (T+{elapsed:.1f}s) 在线={device.online}")
        
        def update():
            # 更新缓存
            self._device_online_cache[device.id] = device.online
            # 直接更新设备 UI，不重建整个网格（避免闪烁）
            self._update_device_ui(device)
            
            # 如果当前正在查看该设备详情，也需要更新连接状态
            if self._selected_device_id == device.id and self.pages["device_detail"]:
               self._update_detail_panel(device)
            
            # 刷新未读消息数量（可能有新的状态变更记录）
            self._update_unread_count()
                
        # 在主线程更新 UI
        self.after(0, update)

    def _update_detail_panel(self, device: Device) -> None:
        """更新详情页连接状态"""
        # 检查是否有实际的详情面板
        if not hasattr(self, '_current_detail_panel') or not self._current_detail_panel:
            return
        
        panel = self._current_detail_panel
            
        if device.type == DeviceType.LIGHT:
            if device.online and device.data:
                panel.update_light_status(
                    power=device.data.get("power", "off"),
                    mode=device.data.get("mode", "static"),
                    r=device.data.get("color_r", 255),
                    g=device.data.get("color_g", 255),
                    b=device.data.get("color_b", 255),
                    connected=True
                )
            else:
                panel.set_disconnected()
        elif device.type == DeviceType.SENSOR:
            if device.online and device.data:
                panel.update_sensor_data(
                    temperature=device.data.get("temperature", 0),
                    tds=device.data.get("tds_value", 0),
                    water_level=device.data.get("water_level", 1),
                    connected=True,
                    wifi_signal=device.data.get("wifi_signal", 0)
                )
            else:
                panel.set_disconnected()
        elif device.is_mijia:
            if device.online and device.data:
                panel.update_status(True, device.data)
            else:
                panel.update_status(False, {})
    
    def _update_device_ui(self, device: Device) -> None:
        """更新设备 UI (局部更新，避免闪烁)"""
        # 计算开启状态
        is_on = False
        # ESP 灯光设备
        if device.online and device.type == DeviceType.LIGHT:
            if device.data.get("power") == "on":
                is_on = True
        # 米家灯光/开关/风扇设备
        elif device.online and device.type in (DeviceType.MIJIA_LIGHT, DeviceType.MIJIA_SWITCH, DeviceType.MIJIA_FAN):
            if device.data.get("power") == "on":
                is_on = True
        
        # 更新设备卡片状态（不重建卡片）
        status_text = device.get_status_text()
        self.pages["devices"].update_device(device.id, device.online, status_text, is_on)
        
        # 如果是多键开关的子设备，也更新多键开关卡片
        if device.did and ".s" in str(device.did):
            self.pages["devices"].update_switch_state(device.id, is_on, is_online=device.online)
            
        # 检查是否为环境传感器设备（如净化器），更新顶部状态栏
        if device.type == DeviceType.MIJIA and ("pm25" in device.data or "temperature" in device.data):
             # 提取并更新顶部状态
             temp = device.data.get("temperature")
             hum = device.data.get("humidity")
             pm25 = device.data.get("pm25")
             # 避免 None 覆盖已有的值(或者这里假定它是主设备)
             self.pages["devices"].update_header_status(temp, hum, pm25)
    
    # ============ 灯光控制回调 (多设备版) ============
    
    def _on_light_power_change_for_device(self, device_id: str, power_on: bool) -> None:
        """灯光开关变化 (指定设备)"""
        device = self.device_manager.get_device(device_id)
        if not device:
            return
        
        client = self.device_manager.get_client(device)
        if client:
            def do_action():
                if power_on:
                    client.turn_on()
                else:
                    client.turn_off()
                # 立即刷新状态
                self.device_manager.poll_device_now(device_id)
            
            threading.Thread(target=do_action, daemon=True).start()
    
    def _on_light_color_change_for_device(self, device_id: str, r: int, g: int, b: int) -> None:
        """灯光颜色变化 (指定设备)"""
        device = self.device_manager.get_device(device_id)
        if not device:
            return
        
        client = self.device_manager.get_client(device)
        if client:
            def do_action():
                client.set_color(r, g, b)
            
            threading.Thread(target=do_action, daemon=True).start()
    
    def _on_light_mode_change_for_device(self, device_id: str, mode: str) -> None:
        """灯光模式变化 (指定设备)"""
        device = self.device_manager.get_device(device_id)
        if not device:
            return
        
        client = self.device_manager.get_client(device)
        if client:
            def do_action():
                client.set_mode(mode)
            
            threading.Thread(target=do_action, daemon=True).start()
    
    # ============ 初始化和调度 ============
    
    def _init_settings(self) -> None:
        """初始化设置"""
        # 设置报警阈值
        min_temp, max_temp = self.config.get_temp_alert_range()
        max_tds = self.config.get_tds_alert()
        self.alert_manager.set_thresholds(min_temp, max_temp, max_tds)
        
        # 初始化鱼缸信息面板
        schedule = self.config.get_schedule()
        self.pages["automation"].set_initial_values(
            min_temp, max_temp, max_tds,
            schedule.get("enable", False),
            schedule.get("on_time", "09:00"),
            schedule.get("off_time", "23:00")
        )
        
        # 设置清除回调
        self.pages["automation"].set_clear_callback(
            self.alert_manager.clear_history
        )
    
    def _start_scheduler(self) -> None:
        """启动调度器"""
        # 设置回调
        self.scheduler.set_schedule_callback(self._on_schedule_action)
        self.alert_manager.set_alert_callback(self._on_alert)
        
        # 配置调度器
        schedule = self.config.get_schedule()
        self.scheduler.set_schedule(
            schedule.get("enable", False),
            schedule.get("on_time", "09:00"),
            schedule.get("off_time", "23:00")
        )
        
        # 启动 (不再使用 scheduler 的刷新，改用 device_manager)
        # self.scheduler.start()
    
    # ============ 鱼缸信息 ============
    
    def _on_alert_settings_change(self, min_temp: float, max_temp: float, max_tds: int) -> None:
        """报警设置变化"""
        self.alert_manager.set_thresholds(min_temp, max_temp, max_tds)
        self.config.set_temp_alert_range(min_temp, max_temp)
        self.config.set_tds_alert(max_tds)
        self.config.save()
    
    def _on_schedule_change(self, enabled: bool, on_time: str, off_time: str) -> None:
        """定时设置变化"""
        self.scheduler.set_schedule(enabled, on_time, off_time)
        self.config.set_schedule(enabled, on_time, off_time)
        self.config.save()
    
    def _on_schedule_action(self, action: str) -> None:
        """定时操作 - 控制所有灯设备"""
        light_devices = self.device_manager.get_devices_by_type(DeviceType.LIGHT)
        
        for device in light_devices:
            client = self.device_manager.get_client(device)
            if client:
                if action == "on":
                    client.turn_on()
                elif action == "off":
                    client.turn_off()
        
        msg = "⏰ 定时开灯" if action == "on" else "⏰ 定时关灯"
        self.pages["automation"].add_alert(f"{msg} ({len(light_devices)} 台设备)")
    
    def _on_alert(self, alert_type: str, message: str) -> None:
        """报警回调"""
        # 添加到日志
        self.after(0, lambda: self.pages["automation"].add_alert(message))
        
        # 播放提示音
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except:
            pass
    
    def _on_close(self) -> None:
        """关闭窗口"""
        try:
            self.device_manager.stop_polling()
            self.device_manager.save_devices()  # 保存设备状态
            self.scheduler.stop()
        except Exception as e:
            print(f"关闭时出错: {e}")
        finally:
            self.destroy()

    # ============ 设置面板回调 ============

    def _on_mijia_bind(self) -> None:
        """米家绑定回调"""
        print("[App] 收到米家绑定请求")
        # 重新同步设备
        self._on_mijia_sync()

    def _on_mijia_unbind(self) -> None:
        """米家解绑回调"""
        print("[App] 收到米家解绑请求")
        # 可以在这里处理解绑后的逻辑，例如刷新界面
        
    def _on_mijia_sync(self) -> None:
        """米家同步设备回调"""
        print("[App] 开始同步米家设备...")
        count = self.device_manager.sync_mijia_devices()
        print(f"[App] 同步完成，新增 {count} 台设备")
        
        # 刷新界面
        self._refresh_device_grid()
        
        # 刷新设置面板的设备列表
        if "settings" in self.pages:
             # 获取最新设备列表传给 settings
            all_devices = self.device_manager.get_all_devices()
            # 转换为 dict 列表
            devices_list = [d.to_dict() for d in all_devices]
            self.pages["settings"].update_device_list(devices_list)
            
            # 同时刷新米家面板状态
            self.pages["settings"].refresh_mijia_status()

    def _on_visibility_change_simple(self, device_id: str, visible: bool) -> None:
        """设备可见性变更"""
        device = self.device_manager.get_device(device_id)
        if device:
            device.visible = visible
            self.device_manager.save_devices()
            print(f"[App] 设备 {device.name} 可见性设置为: {visible}")
            
            # 刷新设备网格
            self._refresh_device_grid()

    def _on_visibility_refresh(self) -> None:
        """可见性面板刷新请求"""
        # 复用同步逻辑
        self._on_mijia_sync()


def run_app():
    """运行应用"""
    app = AquaGuardApp()
    app.mainloop()
