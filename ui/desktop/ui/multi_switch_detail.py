"""
AquaGuard 韩家家庭智能系统 - 多键开关详情页

显示多键开关的详细控制界面，每个按键可独立控制
"""

import customtkinter as ctk
from typing import Callable, Optional, List, Dict
from .theme import Theme


class MultiSwitchDetailPanel(ctk.CTkFrame):
    """
    多键开关详情页
    
    显示多键开关的所有按键，每个按键可独立开关
    """
    
    def __init__(
        self,
        master,
        device_name: str = "多键开关",
        switches: List[Dict] = None,  # [{id, name, is_on}, ...]
        is_online: bool = False,
        on_switch_change: Optional[Callable[[str, bool], None]] = None,
        on_back: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.device_name = device_name
        self.switches = switches or []
        self._is_online = is_online
        self._on_switch_change = on_switch_change
        self._on_back = on_back
        
        # 开关控件引用
        self._switch_widgets: Dict[str, ctk.CTkSwitch] = {}
        self._switch_states: Dict[str, bool] = {}
        
        self.configure(fg_color="transparent")
        
        self._create_ui()
    
    def _create_ui(self):
        # 顶部导航栏
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
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
            command=self._on_back
        )
        back_btn.pack(side="left")
        
        # 标题
        title_label = ctk.CTkLabel(
            nav_frame,
            text=self.device_name,
            font=(Theme.FONT_FAMILY, 20, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title_label.pack(side="left", padx=20)
        
        # 在线状态
        status_text = "在线" if self._is_online else "离线"
        status_color = Theme.ACCENT_PRIMARY if self._is_online else Theme.TEXT_MUTED
        self.status_label = ctk.CTkLabel(
            nav_frame,
            text=status_text,
            font=(Theme.FONT_FAMILY, 12),
            text_color=status_color
        )
        self.status_label.pack(side="right")
        
        # 分隔线
        separator = ctk.CTkFrame(self, fg_color=Theme.BORDER_DEFAULT, height=1)
        separator.pack(fill="x", padx=20, pady=10)
        
        # 开关控制区域
        switches_frame = ctk.CTkFrame(self, fg_color="transparent")
        switches_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 提示文字
        if not self._is_online:
            offline_label = ctk.CTkLabel(
                switches_frame,
                text="设备离线，无法控制",
                font=(Theme.FONT_FAMILY, 14),
                text_color=Theme.TEXT_MUTED
            )
            offline_label.pack(pady=20)
            return
        
        # 创建每个开关的控制行
        for idx, switch in enumerate(self.switches):
            switch_id = switch.get("id", "")
            switch_name = switch.get("name", f"开关 {idx + 1}")
            is_on = switch.get("is_on", False)
            
            self._switch_states[switch_id] = is_on
            
            # 开关行容器
            row_frame = ctk.CTkFrame(
                switches_frame,
                fg_color=Theme.BG_CARD,
                corner_radius=10,
                height=60
            )
            row_frame.pack(fill="x", pady=5)
            row_frame.pack_propagate(False)
            
            # 左侧：开关名称和状态
            left_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            left_frame.pack(side="left", fill="y", padx=15)
            
            name_label = ctk.CTkLabel(
                left_frame,
                text=switch_name,
                font=(Theme.FONT_FAMILY, 14, "bold"),
                text_color=Theme.TEXT_PRIMARY
            )
            name_label.pack(side="left", pady=15)
            
            # 右侧：开关控件
            switch_widget = ctk.CTkSwitch(
                row_frame,
                text="",
                width=50,
                height=26,
                switch_width=45,
                switch_height=22,
                fg_color=Theme.BG_PRIMARY,
                progress_color=Theme.ACCENT_PRIMARY,
                button_color=Theme.TEXT_PRIMARY,
                button_hover_color=Theme.TEXT_SECONDARY,
                command=lambda sid=switch_id: self._on_switch_toggle(sid)
            )
            switch_widget.pack(side="right", padx=15, pady=15)
            
            # 设置初始状态
            if is_on:
                switch_widget.select()
            else:
                switch_widget.deselect()
            
            self._switch_widgets[switch_id] = switch_widget
    
    def _on_switch_toggle(self, switch_id: str):
        """开关切换"""
        if switch_id in self._switch_widgets:
            widget = self._switch_widgets[switch_id]
            new_state = widget.get() == 1
            self._switch_states[switch_id] = new_state
            
            if self._on_switch_change:
                self._on_switch_change(switch_id, new_state)
    
    def update_switch_state(self, switch_id: str, is_on: bool):
        """更新开关状态（外部调用）"""
        if switch_id in self._switch_widgets:
            widget = self._switch_widgets[switch_id]
            self._switch_states[switch_id] = is_on
            if is_on:
                widget.select()
            else:
                widget.deselect()
    
    def update_switches(self, switches: List[Dict]):
        """更新所有开关数据"""
        self.switches = switches
        # 重建 UI
        for widget in self.winfo_children():
            widget.destroy()
        self._switch_widgets.clear()
        self._switch_states.clear()
        self._create_ui()
