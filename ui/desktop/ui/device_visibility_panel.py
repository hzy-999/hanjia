"""
AquaGuard 韩家家庭智能系统 - 设备可见性管理面板

在设置中管理设备的显示/隐藏
"""

import customtkinter as ctk
from typing import Callable, Optional, List, Dict
from .theme import Theme


class DeviceVisibilityPanel(ctk.CTkFrame):
    """
    设备可见性管理面板
    
    显示所有设备列表，可以开关每个设备的可见性
    """
    
    def __init__(
        self,
        master,
        devices: List[Dict] = None,  # [{id, name, visible, type}, ...]
        on_visibility_change: Optional[Callable[[str, bool], None]] = None,
        on_refresh: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.devices = devices or []
        self._on_visibility_change = on_visibility_change
        self._on_refresh = on_refresh
        self._switch_widgets: Dict[str, ctk.CTkSwitch] = {}
        
        self.configure(fg_color="transparent")
        
        self._create_ui()
    
    def _create_ui(self):
        # 标题栏
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 10))
        
        # 标题
        title_label = ctk.CTkLabel(
            title_frame,
            text="📱 设备显示管理",
            font=(Theme.FONT_FAMILY, 14, "bold"),
            text_color=Theme.ACCENT_PRIMARY
        )
        title_label.pack(side="left")
        
        # 刷新按钮 (如果有通过回调)
        if self._on_refresh:
            refresh_btn = ctk.CTkButton(
                title_frame,
                text="🔄",
                width=30,
                height=24,
                fg_color=Theme.BG_CARD,
                hover_color=Theme.BG_CARD_HOVER,
                text_color=Theme.TEXT_PRIMARY,
                command=self._on_refresh
            )
            refresh_btn.pack(side="right")
        
        # 说明文字
        hint_label = ctk.CTkLabel(
            self,
            text="选择要在首页显示的设备：",
            font=(Theme.FONT_FAMILY, 11),
            text_color=Theme.TEXT_SECONDARY
        )
        hint_label.pack(anchor="w", pady=(0, 10))
        
        # 设备列表容器 (带滚动)
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
        """创建单个设备的显示行"""
        device_id = device.get("id", "")
        device_name = device.get("name", "未知设备")
        device_type = device.get("type", "")
        is_visible = device.get("visible", True)
        
        # 行容器
        row_frame = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        row_frame.pack(fill="x", padx=10, pady=3)
        row_frame.pack_propagate(False)
        
        # 设备名称
        name_label = ctk.CTkLabel(
            row_frame,
            text=device_name,
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_PRIMARY
        )
        name_label.pack(side="left", pady=8)
        
        # 设备类型标签
        type_label = ctk.CTkLabel(
            row_frame,
            text=f"({device_type})",
            font=(Theme.FONT_FAMILY, 10),
            text_color=Theme.TEXT_MUTED
        )
        type_label.pack(side="left", padx=(5, 0), pady=8)
        
        # 可见性开关
        switch = ctk.CTkSwitch(
            row_frame,
            text="",
            width=45,
            height=22,
            switch_width=40,
            switch_height=20,
            fg_color=Theme.BG_PRIMARY,
            progress_color=Theme.ACCENT_PRIMARY,
            button_color=Theme.TEXT_PRIMARY,
            button_hover_color=Theme.TEXT_SECONDARY,
            command=lambda did=device_id: self._on_switch_toggle(did)
        )
        switch.pack(side="right", pady=8)
        
        # 设置初始状态
        if is_visible:
            switch.select()
        else:
            switch.deselect()
        
        self._switch_widgets[device_id] = switch
    
    def _on_switch_toggle(self, device_id: str):
        """切换可见性"""
        if device_id in self._switch_widgets:
            widget = self._switch_widgets[device_id]
            new_state = widget.get() == 1
            
            if self._on_visibility_change:
                self._on_visibility_change(device_id, new_state)
    
    def update_devices(self, devices: List[Dict]):
        """更新设备列表"""
        self.devices = devices
        # 重建 UI
        for widget in self.winfo_children():
            widget.destroy()
        self._switch_widgets.clear()
        self._create_ui()
