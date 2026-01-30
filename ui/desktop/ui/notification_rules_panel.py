"""
AquaGuard 韩家家庭智能系统 - 通知规则管理面板
"""

import customtkinter as ctk
from typing import Callable, Optional, List, Dict
from .theme import Theme


class NotificationRulesPanel(ctk.CTkFrame):
    """
    通知规则管理面板
    
    显示所有设备，允许配置开启/关闭时的推送规则
    """
    
    def __init__(
        self,
        master,
        devices: List[Dict] = None,  # [{id, name, type, ...}]
        rules: Dict[str, Dict] = None, # {device_id: {"on": bool, "off": bool}}
        on_rule_change: Optional[Callable[[str, str, bool], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.devices = devices or []
        self.rules = rules or {}
        self._on_rule_change = on_rule_change
        
        self.configure(fg_color="transparent")
        
        self._create_ui()
    
    def _create_ui(self):
        # 说明文字
        hint_label = ctk.CTkLabel(
            self,
            text="选择要接收通知的设备状态：",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY
        )
        hint_label.pack(anchor="w", pady=(0, 10))
        
        # 列表容器 (带滚动)
        list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=Theme.BG_CARD,
            corner_radius=10,
            height=200
        )
        list_frame.pack(fill="x", expand=False)
        
        if not self.devices:
            no_device_label = ctk.CTkLabel(
                list_frame,
                text="暂无设备",
                font=(Theme.FONT_FAMILY, 12),
                text_color=Theme.TEXT_MUTED
            )
            no_device_label.pack(pady=20)
            return
        
        # 创建设备行
        for device in self.devices:
            self._create_device_row(list_frame, device)
    
    def _create_device_row(self, parent, device: Dict):
        """创建单个设备的规则行"""
        device_id = device.get("id", "")
        device_name = device.get("name", "未知设备")
        
        # 获取当前规则
        device_rule = self.rules.get(device_id, {})
        notify_on = device_rule.get("on", False)
        notify_off = device_rule.get("off", False)
        
        # 行容器
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=5, pady=2)
        
        # 设备名称
        name_label = ctk.CTkLabel(
            row_frame,
            text=device_name,
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_PRIMARY,
            width=150,
            anchor="w"
        )
        name_label.pack(side="left", padx=5)
        
        # 开启通知 Checkbox
        on_cb = ctk.CTkCheckBox(
            row_frame,
            text="开启时通知",
            font=(Theme.FONT_FAMILY, 11),
            text_color=Theme.TEXT_SECONDARY,
            checkbox_width=20,
            checkbox_height=20,
            width=100,
            command=lambda: self._on_cb_change(device_id, "on", on_cb)
        )
        on_cb.pack(side="left", padx=10)
        if notify_on:
            on_cb.select()
        else:
            on_cb.deselect()
            
        # 关闭通知 Checkbox
        off_cb = ctk.CTkCheckBox(
            row_frame,
            text="关闭时通知",
            font=(Theme.FONT_FAMILY, 11),
            text_color=Theme.TEXT_SECONDARY,
            checkbox_width=20,
            checkbox_height=20,
            width=100,
            command=lambda: self._on_cb_change(device_id, "off", off_cb)
        )
        off_cb.pack(side="left", padx=10)
        if notify_off:
            off_cb.select()
        else:
            off_cb.deselect()
            
    def _on_cb_change(self, device_id, action_key, widget):
        """复选框变化回调"""
        is_checked = widget.get() == 1
        if self._on_rule_change:
            self._on_rule_change(device_id, action_key, is_checked)
            
    def update_data(self, devices: List[Dict], rules: Dict):
        """更新数据"""
        self.devices = devices
        self.rules = rules
        # 重建 UI
        for widget in self.winfo_children():
            widget.destroy()
        self._create_ui()
