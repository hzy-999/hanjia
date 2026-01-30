"""
AquaGuard 韩家家庭智能系统 - 灯光控制模块

提供 RGB 拾色器和场景模式切换
"""

import customtkinter as ctk
from typing import Callable, Optional, Tuple
from .theme import Theme


class BrightnessControl(ctk.CTkFrame):
    """亮度控制器 (替代 RGB 拾色器)"""
    
    def __init__(self, master, on_color_change: Optional[Callable[[int, int, int], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color=Theme.BG_CARD, corner_radius=Theme.CORNER_RADIUS)
        self.on_color_change = on_color_change
        
        self._brightness = 255
        
        # 标题
        self.title = ctk.CTkLabel(
            self,
            text="💡 亮度调节",
            font=(Theme.FONT_FAMILY, 14, "bold"),
            text_color=Theme.ACCENT_PRIMARY
        )
        self.title.pack(pady=(20, 10))
        
        # 亮度百分比显示
        self.percent_label = ctk.CTkLabel(
            self,
            text="100%",
            font=("Roboto", 48, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        self.percent_label.pack(pady=20)
        
        # 滑块容器
        self.slider_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.slider_frame.pack(fill="x", padx=30, pady=20)
        
        # 亮度滑块
        self.slider = ctk.CTkSlider(
            self.slider_frame,
            from_=0,
            to=255,
            number_of_steps=255,
            progress_color=Theme.ACCENT_PRIMARY,
            button_color=Theme.ACCENT_PRIMARY,
            command=self._on_slider_change
        )
        self.slider.set(255)
        self.slider.pack(fill="x")
        
        # 底部提示
        ctk.CTkLabel(
            self,
            text="拖动调节灯光亮度",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY
        ).pack(side="bottom", pady=20)
        
    def _on_slider_change(self, value: float) -> None:
        """滑块值变化"""
        self._brightness = int(value)
        
        # 更新显示
        percent = int((self._brightness / 255) * 100)
        self.percent_label.configure(text=f"{percent}%")
        
        # 这里的关键是：单色灯模式下，我们将 R=G=B=亮度
        # 这样兼容底层的 RGB 协议，同时 simple_led 固件会取平均值作为亮度
        if self.on_color_change:
            self.on_color_change(self._brightness, self._brightness, self._brightness)
            
    def set_color(self, r: int, g: int, b: int) -> None:
        """设置颜色 (反推亮度)"""
        # 取最大值作为亮度
        brightness = max(r, g, b)
        self._brightness = brightness
        self.slider.set(brightness)
        
        percent = int((brightness / 255) * 100)
        self.percent_label.configure(text=f"{percent}%")
        
    def get_color(self) -> Tuple[int, int, int]:
        """获取当前颜色"""
        return (self._brightness, self._brightness, self._brightness)


class SceneModeCard(ctk.CTkFrame):
    """场景模式卡片"""
    
    def __init__(self, master, icon: str, title: str, description: str,
                 color: str, on_click: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.CORNER_RADIUS,
            cursor="hand2"
        )
        self.on_click = on_click
        self._selected = False
        
        # 绑定点击事件
        self.bind("<Button-1>", self._handle_click)
        
        # 图标
        self.icon_label = ctk.CTkLabel(
            self,
            text=icon,
            font=("", 32)
        )
        self.icon_label.pack(pady=(15, 5))
        self.icon_label.bind("<Button-1>", self._handle_click)
        
        # 标题
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=(Theme.FONT_FAMILY, 14, "bold"),
            text_color=color
        )
        self.title_label.pack(pady=2)
        self.title_label.bind("<Button-1>", self._handle_click)
        
        # 描述
        self.desc_label = ctk.CTkLabel(
            self,
            text=description,
            font=(Theme.FONT_FAMILY, 10),
            text_color=Theme.TEXT_MUTED
        )
        self.desc_label.pack(pady=(0, 15))
        self.desc_label.bind("<Button-1>", self._handle_click)
        
        self._highlight_color = color
    
    def _handle_click(self, event=None) -> None:
        """处理点击"""
        if self.on_click:
            self.on_click()
    
    def set_selected(self, selected: bool) -> None:
        """设置选中状态"""
        self._selected = selected
        if selected:
            # 激活状态：加边框，背景保持白/卡片色
            self.configure(fg_color=Theme.BG_CARD, border_width=2, border_color=self._highlight_color)
        else:
            self.configure(fg_color=Theme.BG_CARD, border_width=0)


class LightingPanel(ctk.CTkFrame):
    """灯光控制面板"""
    
    def __init__(self, master, 
                 on_power_change: Optional[Callable[[bool], None]] = None,
                 on_color_change: Optional[Callable[[int, int, int], None]] = None,
                 on_mode_change: Optional[Callable[[str], None]] = None,
                 **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="transparent")
        
        self.on_power_change = on_power_change
        self.on_color_change = on_color_change
        self.on_mode_change = on_mode_change
        
        self._power_on = False
        self._current_mode = "static"
        
        # 标题 (与 Dashboard 统一风格)
        title_box = ctk.CTkFrame(self, fg_color="transparent")
        title_box.pack(fill="x", padx=30, pady=(30, 20))
        
        title = ctk.CTkLabel(
            title_box,
            text="灯光指挥台",
            font=(Theme.FONT_FAMILY, 26, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title.pack(anchor="w")
        
        # 连接状态和开关 (控制栏)
        self.control_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=Theme.CORNER_RADIUS)
        self.control_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.connection_label = ctk.CTkLabel(
            self.control_frame,
            text="⚪ 灯光节点: 未连接",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_MUTED
        )
        self.connection_label.pack(side="left", padx=20, pady=15)
        
        self.power_switch = ctk.CTkSwitch(
            self.control_frame,
            text="总开关",
            font=(Theme.FONT_FAMILY, 12),
            command=self._on_power_toggle,
            progress_color=Theme.ACCENT_PRIMARY,
            button_color=Theme.ACCENT_PRIMARY,
            text_color=Theme.TEXT_PRIMARY
        )
        self.power_switch.pack(side="right", padx=20, pady=15)
        
        # 主要内容区
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20)
        
        # 左侧：亮度控制器
        self.color_picker = BrightnessControl(
            self.content_frame,
            on_color_change=self._handle_color_change
        )
        self.color_picker.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 右侧：场景模式
        self.modes_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.modes_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        self.modes_title = ctk.CTkLabel(
            self.modes_frame,
            text="🎭 场景模式",
            font=(Theme.FONT_FAMILY, 14, "bold"),
            text_color=Theme.ACCENT_PRIMARY
        )
        self.modes_title.pack(pady=(0, 10))
        
        # 场景卡片
        self.scene_cards = {}
        
        # 针对单色灯优化的场景
        scenes = [
            ("daylight", "🌞", "高亮模式", "100% 全亮度照明", Theme.COLOR_SUNNY),
            ("moonlight", "🌙", "微光模式", "20% 低亮度氛围", Theme.COLOR_BLUE),
            ("aurora", "✨", "呼吸模式", "缓慢呼吸效果", Theme.COLOR_PURPLE),
        ]
        
        for mode_id, icon, title, desc, color in scenes:
            card = SceneModeCard(
                self.modes_frame,
                icon=icon,
                title=title,
                description=desc,
                color=color,
                on_click=lambda m=mode_id: self._on_scene_select(m)
            )
            card.pack(fill="x", pady=5)
            self.scene_cards[mode_id] = card
        
        # 模式选择
        self.mode_frame = ctk.CTkFrame(self.modes_frame, fg_color=Theme.BG_CARD, corner_radius=Theme.CORNER_RADIUS)
        self.mode_frame.pack(fill="x", pady=(15, 0))
        
        mode_label = ctk.CTkLabel(
            self.mode_frame,
            text="灯光效果:",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY
        )
        mode_label.pack(side="left", padx=15, pady=15)
        
        self.mode_menu = ctk.CTkOptionMenu(
            self.mode_frame,
            values=["静态", "彩虹渐变", "呼吸效果"],
            command=self._on_mode_select,
            fg_color=Theme.BG_PRIMARY,
            button_color=Theme.ACCENT_PRIMARY,
            button_hover_color=Theme.ACCENT_HOVER,
            dropdown_fg_color=Theme.BG_CARD,
            text_color=Theme.TEXT_PRIMARY
        )
        self.mode_menu.pack(side="right", padx=15, pady=15)
    
    def _on_power_toggle(self) -> None:
        """开关切换"""
        self._power_on = self.power_switch.get()
        if self.on_power_change:
            self.on_power_change(self._power_on)
    
    def _handle_color_change(self, r: int, g: int, b: int) -> None:
        """颜色变化处理"""
        # 取消场景选择
        for card in self.scene_cards.values():
            card.set_selected(False)
        
        if self.on_color_change:
            self.on_color_change(r, g, b)
    
    def _on_scene_select(self, scene: str) -> None:
        """场景选择"""
        # 更新选中状态
        for mode_id, card in self.scene_cards.items():
            card.set_selected(mode_id == scene)
        
        # 设置预设颜色和模式
        if scene == "daylight":
            self.color_picker.set_color(255, 255, 255)
            mode = "static"
        elif scene == "moonlight":
            # 20% 亮度 -> ~50/255
            self.color_picker.set_color(50, 50, 50)
            mode = "static"
        elif scene == "aurora":
            mode = "breath" # 注意：单色灯只有呼吸，没有彩虹
        else:
            mode = "static"
        
        self._current_mode = mode
        self._update_mode_menu(mode)
        
        if self.on_mode_change:
            self.on_mode_change(mode)
        
        # 同时发送颜色（如果不是彩虹模式）
        if mode == "static" and self.on_color_change:
            r, g, b = self.color_picker.get_color()
            self.on_color_change(r, g, b)
    
    def _on_mode_select(self, mode_name: str) -> None:
        """模式选择"""
        mode_map = {
            "静态": "static",
            "彩虹渐变": "rainbow",
            "呼吸效果": "breath"
        }
        mode = mode_map.get(mode_name, "static")
        self._current_mode = mode
        
        # 取消场景选择
        for card in self.scene_cards.values():
            card.set_selected(False)
        
        if self.on_mode_change:
            self.on_mode_change(mode)
    
    def _update_mode_menu(self, mode: str) -> None:
        """更新模式下拉菜单"""
        mode_names = {
            "static": "静态",
            "rainbow": "彩虹渐变",
            "breath": "呼吸效果"
        }
        self.mode_menu.set(mode_names.get(mode, "静态"))
    
    def update_light_status(self, power: str, mode: str, r: int, g: int, b: int,
                           connected: bool) -> None:
        """更新灯光状态"""
        # 更新连接状态
        if connected:
            self.connection_label.configure(
                text="🟢 灯光节点: 已连接",
                text_color=Theme.ACCENT_SUCCESS
            )
        else:
            self.connection_label.configure(
                text="🔴 灯光节点: 未连接",
                text_color=Theme.ACCENT_ERROR
            )
        
        # 更新开关状态
        self._power_on = power == "on"
        if self._power_on:
            self.power_switch.select()
        else:
            self.power_switch.deselect()
        
        # 更新模式
        self._current_mode = mode
        self._update_mode_menu(mode)
        
        # 更新颜色（避免触发回调）
        self.color_picker.set_color(r, g, b)
    
    def set_disconnected(self) -> None:
        """设置为断开状态"""
        self.connection_label.configure(
            text="🔴 灯光节点: 未连接",
            text_color=Theme.ACCENT_ERROR
        )
