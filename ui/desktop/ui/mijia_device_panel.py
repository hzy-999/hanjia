import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from .theme import Theme

class MijiaDevicePanel(ctk.CTkFrame):
    """米家设备通用控制面板"""
    
    def __init__(self, master, device_name: str, device_model: str,
                 on_power_change: Optional[Callable[[bool], None]] = None,
                 **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="transparent")
        
        self.on_power_change = on_power_change
        self._power_on = False
        
        # 标题区域
        title_box = ctk.CTkFrame(self, fg_color="transparent")
        title_box.pack(fill="x", padx=30, pady=(30, 20))
        
        self.title_label = ctk.CTkLabel(
            title_box,
            text=device_name,
            font=(Theme.FONT_FAMILY, 24, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.title_label.pack(anchor="w")
        
        ctk.CTkLabel(
            title_box,
            text=f"型号: {device_model}",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(5, 0))
        
        # 控制区域
        self.control_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=Theme.CORNER_RADIUS)
        self.control_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # 连接状态
        self.connection_label = ctk.CTkLabel(
            self.control_frame,
            text="⚪ 设备未连接",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_MUTED
        )
        self.connection_label.pack(side="left", padx=20, pady=20)
        
        # 开关按钮
        self.power_switch = ctk.CTkSwitch(
            self.control_frame,
            text="设备电源",
            font=(Theme.FONT_FAMILY, 12),
            command=self._on_power_toggle,
            progress_color=Theme.ACCENT_PRIMARY,
            button_color=Theme.ACCENT_PRIMARY,
            text_color=Theme.TEXT_PRIMARY
        )
        self.power_switch.pack(side="right", padx=20, pady=20)
        
        # 属性显示区域
        self.props_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=Theme.CORNER_RADIUS)
        self.props_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            self.props_frame,
            text="设备状态",
            font=(Theme.FONT_FAMILY, 14, "bold"),
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=15)
        
        self.props_container = ctk.CTkFrame(self.props_frame, fg_color="transparent")
        self.props_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.prop_labels = {}
    
    def _on_power_toggle(self) -> None:
        """开关切换"""
        self._power_on = self.power_switch.get()
        if self.on_power_change:
            self.on_power_change(self._power_on)
    
    def update_status(self, connected: bool, data: Dict[str, Any]) -> None:
        """更新设备状态"""
        # 更新连接状态
        if connected:
            self.connection_label.configure(
                text="🟢 设备已连接",
                text_color=Theme.ACCENT_SUCCESS
            )
            self.power_switch.configure(state="normal")
        else:
            self.connection_label.configure(
                text="🔴 设备离线",
                text_color=Theme.ACCENT_ERROR
            )
            self.power_switch.configure(state="disabled")
        
        # 更新开关状态
        power = data.get("power", "off")
        self._power_on = power == "on"
        if self._power_on:
            self.power_switch.select()
        else:
            self.power_switch.deselect()
        
        # 更新属性列表
        self._update_props(data)
    
    def _update_props(self, data: Dict[str, Any]) -> None:
        """更新属性列表显示"""
        # 清除旧属性
        for widget in self.props_container.winfo_children():
            widget.destroy()
            
        # 常见属性映射
        prop_map = {
            "power": "电源状态",
            "brightness": "亮度",
            "color_temperature": "色温",
            "fan_level": "风速档位",
            "temperature": "温度",
            "humidity": "湿度",
            "pm25": "PM2.5",
            "mode": "模式"
        }
        
        row = 0
        for key, value in data.items():
            if key == "online":
                continue
                
            label_text = prop_map.get(key, key)
            
            # 创建行
            row_frame = ctk.CTkFrame(self.props_container, fg_color="transparent", height=30)
            row_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                row_frame,
                text=f"{label_text}:",
                font=(Theme.FONT_FAMILY, 12),
                text_color=Theme.TEXT_SECONDARY,
                width=100,
                anchor="w"
            ).pack(side="left")
            
            ctk.CTkLabel(
                row_frame,
                text=str(value),
                font=(Theme.FONT_FAMILY, 12, "bold"),
                text_color=Theme.TEXT_PRIMARY
            ).pack(side="left", padx=10)
