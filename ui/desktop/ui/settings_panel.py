"""
AquaGuard 设置面板组件
"""

import customtkinter as ctk
import tkinter.messagebox
from typing import Optional

from .theme import Theme
from .mijia_login_dialog import MijiaSettingsPanel

class SettingsPanel(ctk.CTkFrame):
    """系统设置面板 (嵌入主窗口)"""
    
    def __init__(self, master, config, device_manager=None, config_manager=None, on_save: Optional[callable] = None, **kwargs):
        super().__init__(master, fg_color=Theme.BG_SECONDARY, **kwargs)
        
        self.config = config
        self.device_manager = device_manager
        self.config_manager = config_manager  # 保存 config_manager 引用
        self.on_save = on_save
        
        # 主框架 (带滚动)
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        ctk.CTkLabel(
            self.main_scroll,
            text="⚙️ 系统设置",
            font=(Theme.FONT_FAMILY, 24, "bold"),
            text_color=Theme.ACCENT_PRIMARY
        ).pack(pady=(0, 30), anchor="w")
        
        # --- 基础设置 ---
        self._create_section_title("基础设置")
        
        # 刷新间隔
        interval_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        interval_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            interval_frame,
            text="数据刷新间隔 (毫秒):",
            font=(Theme.FONT_FAMILY, 14),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")
        
        self.interval_entry = ctk.CTkEntry(
            interval_frame,
            placeholder_text="3000",
            fg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            height=35
        )
        self.interval_entry.pack(fill="x", pady=(5, 10))
        self.interval_entry.insert(0, str(config.get_refresh_interval()))

        # 鱼缸节点 IP 设置
        fish_ip_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        fish_ip_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            fish_ip_frame,
            text="鱼缸节点 IP:",
            font=(Theme.FONT_FAMILY, 14),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        self.fish_ip_entry = ctk.CTkEntry(
            fish_ip_frame,
            placeholder_text="192.168.31.161",
            fg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY,
            height=35
        )
        self.fish_ip_entry.pack(fill="x", pady=(5, 10))
        self.fish_ip_entry.insert(0, config.get_fish_tank_ip())

        # 状态变更记录开关
        status_log_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        status_log_frame.pack(fill="x", pady=5)
        
        self.status_log_var = ctk.BooleanVar(value=config.is_status_log_enabled())
        
        self.status_log_switch = ctk.CTkSwitch(
            status_log_frame,
            text="启用设备状态变更记录",
            variable=self.status_log_var,
            font=(Theme.FONT_FAMILY, 14),
            text_color=Theme.TEXT_SECONDARY
        )
        self.status_log_switch.pack(anchor="w", pady=(5, 5))
        
        ctk.CTkLabel(
            status_log_frame,
            text="* 开启后，设备状态变更会记录在首页🔔按钮中",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 10))

        # --- 米家设置 ---
        self._create_separator()
        self._create_section_title("米家接入")
        
        if device_manager:
            self.mijia_panel = MijiaSettingsPanel(
                self.main_scroll,
                device_manager,
                on_bind=self._on_mijia_bind_req,
                on_unbind=self._on_mijia_unbind_req,
                on_sync=self._on_mijia_sync_req
            )
            self.mijia_panel.pack(fill="x", pady=5)

        # --- 设备可见性 ---
        self._create_separator()
        self._create_section_title("设备显示管理")
        
        if device_manager:
            from .device_visibility_panel import DeviceVisibilityPanel
            
            # 获取设备列表 (需要 App 传入或通过 callback 获取)
            # 优先从 DeviceManager 获取已加载的设备
            self.device_list = []
            if device_manager:
                devices = device_manager.get_all_devices()
                self.device_list = [d.to_dict() for d in devices]
            
            self.visibility_panel = DeviceVisibilityPanel(
                self.main_scroll,
                devices=self.device_list,
                on_visibility_change=self._on_vis_change_internal,
                on_refresh=self._on_vis_refresh_internal
            )
            self.visibility_panel.pack(fill="x", pady=5)

        # --- 通知设置 ---
        self._create_separator()
        self._create_section_title("微信通知 (PushPlus)")
        
        notify_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        notify_frame.pack(fill="x", pady=5)
        
        # 启用开关
        notify_config = self.config.get_notification_config()
        self.notify_enable_var = ctk.BooleanVar(value=notify_config.get("enabled", False))
        
        self.notify_switch = ctk.CTkSwitch(
            notify_frame,
            text="启用设备状态变更推送",
            variable=self.notify_enable_var,
            font=(Theme.FONT_FAMILY, 14),
            text_color=Theme.TEXT_SECONDARY
        )
        self.notify_switch.pack(anchor="w", pady=(5, 10))

        # Token 输入框
        ctk.CTkLabel(
            notify_frame,
            text="PushPlus Token:",
            font=(Theme.FONT_FAMILY, 14),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")

        self.token_entry = ctk.CTkEntry(
            notify_frame,
            placeholder_text="请输入您的 PushPlus Token",
            height=35,
            fg_color=Theme.BG_CARD,
            border_color=Theme.BORDER_DEFAULT,
            text_color=Theme.TEXT_PRIMARY
        )
        self.token_entry.pack(fill="x", pady=(5, 5))
        self.token_entry.insert(0, notify_config.get("token", ""))
        
        ctk.CTkLabel(
            notify_frame,
            text="* 关注 PushPlus 公众号获取 Token，免费接收消息",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 10))

        if self.device_manager:
            from .notification_rules_panel import NotificationRulesPanel
            
            # 获取通知规则
            rules = self.config.get_notification_rules()
            
            self.rules_panel = NotificationRulesPanel(
                self.main_scroll,
                devices=self.device_list,
                rules=rules,
                on_rule_change=self._on_rule_change_internal
            )
            self.rules_panel.pack(fill="x", pady=5)

        # --- 底部按钮区 (固定在底部) ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        btn_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="保存所有设置",
            fg_color=Theme.ACCENT_PRIMARY,
            text_color="#FFFFFF",
            font=(Theme.FONT_FAMILY, 15, "bold"),
            hover_color=Theme.ACCENT_HOVER,
            height=40,
            command=self._on_save_click
        )
        save_btn.pack(side="right", padx=10)
        
        # 回调占位
        self._app_bind_callback = None
        self._app_unbind_callback = None
        self._app_sync_callback = None
        self._app_vis_change_callback = None
        self._app_vis_refresh_callback = None
        
        # 临时存储规则变更 (直到保存)
        self._pending_rules = rules # 直接操作 dict 引用，或者 copy

    def _create_section_title(self, text):
        ctk.CTkLabel(
            self.main_scroll,
            text=text,
            font=(Theme.FONT_FAMILY, 18, "bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", pady=(10, 5))

    def _create_separator(self):
        ctk.CTkFrame(self.main_scroll, fg_color=Theme.BORDER_DEFAULT, height=1).pack(fill="x", pady=20)

    # --- 事件转发 ---
    def set_callbacks(self, on_bind, on_unbind, on_sync, on_vis_change, on_vis_refresh):
        self._app_bind_callback = on_bind
        self._app_unbind_callback = on_unbind
        self._app_sync_callback = on_sync
        self._app_vis_change_callback = on_vis_change
        self._app_vis_refresh_callback = on_vis_refresh

    def update_device_list(self, devices):
        """更新可见性面板的设备列表"""
        self.device_list = devices
        if hasattr(self, 'visibility_panel'):
            self.visibility_panel.update_devices(devices)
        
        # 同时更新通知规则面板
        if hasattr(self, 'rules_panel'):
            # 需要重新合并规则
            current_rules = self.config.get_notification_rules()
            # 如果有未保存的变更，应该合并进来 (简化起见，这里重新读取配置)
            self.rules_panel.update_data(devices, current_rules)

    def refresh_mijia_status(self):
        if hasattr(self, 'mijia_panel'):
            self.mijia_panel.refresh()

    def _on_mijia_bind_req(self):
        if self._app_bind_callback:
            self._app_bind_callback()

    def _on_mijia_unbind_req(self):
        if self._app_unbind_callback:
            self._app_unbind_callback()

    def _on_mijia_sync_req(self):
        if self._app_sync_callback:
            self._app_sync_callback()

    def _on_vis_change_internal(self, did, vis):
        if self._app_vis_change_callback:
            self._app_vis_change_callback(did, vis)
            
    def _on_vis_refresh_internal(self):
        if self._app_vis_refresh_callback:
            self._app_vis_refresh_callback()
            
    def _on_rule_change_internal(self, device_id, action_key, is_checked):
        """通知规则变更 (暂存)"""
        # 这里的 modifying self._pending_rules 实际上是直接修改了 self.config loading 出来的 dict 引用
        # 只要最后调用 save 就行。但为了安全，最好明确 set 回去。
        if device_id not in self._pending_rules:
            self._pending_rules[device_id] = {}
        self._pending_rules[device_id][action_key] = is_checked

    def _on_save_click(self):
        """保存并通知 App"""
        try:
            # 1. 保存刷新间隔
            interval = int(self.interval_entry.get())
            self.config.set_refresh_interval(interval)

            # 保存鱼缸 IP
            fish_ip = self.fish_ip_entry.get().strip()
            self.config.set_fish_tank_ip(fish_ip)

            # 2. 保存通知设置
            if self.config_manager:
                token = self.token_entry.get().strip()
                enabled = self.notify_enable_var.get()
                self.config_manager.set_notification_config(token, enabled)
                
                # 保存通知规则
                self.config_manager.set_notification_rules(self._pending_rules)
                
                # 立即应用到 DeviceManager
                if self.device_manager and hasattr(self.device_manager, '_notification_service'):
                    self.device_manager._notification_service.set_config(token, enabled)

            # 3. 保存状态变更记录开关
            if self.config_manager:
                status_log_enabled = self.status_log_var.get()
                self.config_manager.set_status_log_enabled(status_log_enabled)

            # 4. 持久化
            self.config.save()
            
            # 4. 通知 App 更新运行时状态
            if self.on_save:
                self.on_save()
                
            tkinter.messagebox.showinfo("提示", "设置已保存！")
            
        except ValueError:
            tkinter.messagebox.showerror("错误", "刷新间隔请输入有效的数字")
        except Exception as e:
            tkinter.messagebox.showerror("错误", f"保存失败: {str(e)}")
