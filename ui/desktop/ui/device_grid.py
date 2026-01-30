"""
AquaGuard 韩家家庭智能系统 - 主仪表盘 (Dashboard Style)

参考 Henry's Home 设计：顶部状态 + 场景按钮 + 设备网格
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict, List

from .device_card import DeviceCard, AddDeviceCard
from .scene_button import SceneButton
from .theme import Theme


class DeviceGridPanel(ctk.CTkFrame):
    """
    主仪表盘面板
    """
    
    def __init__(
        self,
        master,
        on_device_click: Optional[Callable[[str], None]] = None,
        on_device_menu: Optional[Callable[[str], None]] = None,
        on_add_device: Optional[Callable[[], None]] = None,
        on_notification_click: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self._on_device_click = on_device_click
        self._on_device_menu = on_device_menu
        self._on_add_device = on_add_device
        self._on_notification_click = on_notification_click
        
        self._device_cards: Dict[str, DeviceCard] = {}
        self._unread_count = 0
        
        # 使用透明背景，透出 app 的 BG_PRIMARY (Gray 300)
        self.configure(fg_color="transparent")
        
        # --- 1. 顶部 Header (Title + Status) ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(30, 20))
        
        # 左侧：标题
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")
        
        title = ctk.CTkLabel(
            title_box,
            text="Henry's Home", # 以后可从配置读取
            font=(Theme.FONT_FAMILY, 26, "bold"),
            text_color=Theme.TEXT_PRIMARY
        )
        title.pack(anchor="w")
        
        # 状态行 (Temp, Humidity, Air)
        self.status_row = ctk.CTkFrame(title_box, fg_color="transparent")
        self.status_row.pack(anchor="w", pady=(5, 0))
        
        # 初始化为空，等待数据更新
        self._status_widgets = {}
        self._create_status_item("temp", "🌡️", "--°C")
        self._create_status_item("hum", "💧", "--%")
        self._create_status_item("air", "🍃", "--")


        
        # 右侧：通知按钮容器（用于放置小红点）
        self.notif_container = ctk.CTkFrame(header_frame, fg_color="transparent", width=64, height=60)
        self.notif_container.pack(side="right")
        self.notif_container.pack_propagate(False)
        
        # 通知按钮（无背景，只显示图标）
        self.notif_btn = ctk.CTkButton(
            self.notif_container,
            text="🔔",
            font=(Theme.FONT_EMOJI, 24),
            width=50,
            height=50,
            fg_color=Theme.BG_SECONDARY,
            hover_color=Theme.BG_SECONDARY,  # 与背景色相同，无悬停效果
            text_color=Theme.TEXT_SECONDARY,
            command=self._handle_notification_click
        )
        self.notif_btn.pack(expand=True)
        
        # 绑定悬停变色效果（只改变图标颜色）
        self.notif_btn.bind("<Enter>", lambda e: self.notif_btn.configure(text_color=Theme.TEXT_PRIMARY))
        self.notif_btn.bind("<Leave>", lambda e: self.notif_btn.configure(text_color=Theme.TEXT_SECONDARY))
        
        # 未读小红点
        self.unread_badge = ctk.CTkLabel(
            self.notif_container,
            text="",
            font=(Theme.FONT_FAMILY, 8, "bold"),
            text_color="#FFFFFF",
            fg_color=Theme.ACCENT_ERROR,
            corner_radius=8,
            width=16,
            height=16
        )
        # 初始隐藏
        self.unread_badge.place_forget()
        
        # --- 2. 场景按钮行 ---
        
        # --- 2. 场景按钮行 ---
        scene_frame = ctk.CTkFrame(self, fg_color="transparent")
        scene_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        # 场景列表
        scenes = [
            ("☀️", "起床", Theme.COLOR_SUNNY),
            ("🚪", "离家", Theme.COLOR_BLUE),
            ("🚗", "回家", Theme.COLOR_INDIGO),
            ("🌙", "晚安", Theme.COLOR_PURPLE),
        ]
        
        for icon, text, color in scenes:
            btn = SceneButton(
                scene_frame,
                icon=icon,
                text=text,
                icon_color=color,
                command=lambda t=text: print(f"Scene {t} triggered")
            )
            btn.pack(side="left", padx=(0, 15))
            
        # --- 3. 设备网格 (Scrollable) ---
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent", # 透明
            scrollbar_button_color=Theme.BG_CARD,
            scrollbar_button_hover_color=Theme.BG_CARD_HOVER,
            width=900
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 网格容器
        self.grid_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True)
        
        # 配置网格列权重 (4列布局, 对应 CSS grid-cols-4)
        for i in range(4):
            self.grid_frame.columnconfigure(i, weight=1, minsize=160) # 稍宽一点
            

    
    def update_unread_count(self, count: int) -> None:
        """更新未读消息数量"""
        self._unread_count = count
        if count > 0:
            # 显示数字，超过99显示99+
            display = str(count) if count <= 99 else "99+"
    def update_unread_count(self, count: int) -> None:
        """更新未读消息数量"""
        self._unread_count = count
        if count > 0:
            # 显示数字，超过99显示99+
            display = str(count) if count <= 99 else "99+"
            self.unread_badge.configure(text=display)
            self.unread_badge.place(x=38, y=4)  # 位于按钮右上角，向内收缩
        else:
            self.unread_badge.place_forget()
    
    def _handle_notification_click(self):
        """处理通知按钮点击"""
        if self._on_notification_click:
            self._on_notification_click()
    
    def _group_multi_switches(self, devices: List[dict]) -> tuple:
        """
        将多键开关的子开关分组
        
        Returns:
            (grouped_switches, regular_devices)
            - grouped_switches: {real_did: [switch1, switch2, ...]}
            - regular_devices: 普通设备列表
        """
        from .multi_switch_card import MultiSwitchCard
        
        grouped = {}  # real_did -> [sub_switches]
        regular = []
        
        for device in devices:
            did = device.get("did", "")
            # 检查是否为虚拟开关 (包含 .s)
            if ".s" in str(did):
                parts = str(did).split(".")
                real_did = parts[0]
                if real_did not in grouped:
                    grouped[real_did] = []
                grouped[real_did].append(device)
            else:
                # 检查是否为多键开关主设备 (有子设备的)
                # 如果已经在 grouped 中有子设备，则跳过主设备
                # 否则作为普通设备
                is_main_switch = any(str(d.get("did", "")).startswith(f"{did}.") for d in devices)
                if not is_main_switch:
                    regular.append(device)
        
        return grouped, regular
    
    def set_devices(self, devices: List[dict], on_switch_click=None) -> None:
        import time
        t_start = time.time()
        
        from .multi_switch_card import MultiSwitchCard
        
        # 1. 数据准备与分组
        grouped_switches, regular_devices = self._group_multi_switches(devices)
        
        # 2. Diff Regular Devices (普通设备)
        current_ids = set(self._device_cards.keys())
        target_ids = {d["id"] for d in regular_devices}
        
        # Remove
        for did in current_ids - target_ids:
            self._device_cards[did].destroy()
            del self._device_cards[did]
            
        # Add
        for did in target_ids - current_ids:
            # 查找对应的数据对象
            device_data = next(d for d in regular_devices if d["id"] == did)
            card = DeviceCard(
                self.grid_frame,
                device_id=device_data["id"],
                device_name=device_data["name"],
                device_icon=device_data["icon"],
                device_color=device_data["color"],
                is_online=device_data["online"],
                status_text=device_data["status_text"],
                is_on=device_data["is_on"],
                on_click=self._on_device_click,
                on_long_press=self._on_device_menu
            )
            self._device_cards[did] = card
            
        # 3. Diff Multi-Switch Cards (多键开关)
        if not hasattr(self, '_multi_switch_cards'):
            self._multi_switch_cards = {}
            
        current_multi_ids = set(self._multi_switch_cards.keys())
        target_multi_ids = set(grouped_switches.keys())
        
        # Remove
        for did in current_multi_ids - target_multi_ids:
            self._multi_switch_cards[did].destroy()
            del self._multi_switch_cards[did]
            
        # Add & Update Data Structure
        # 注意：多键开关需要先准备好 switches 数据
        multi_card_data = {} # {real_did: {name, icon, color, switches, is_online}}
        
        for real_did in target_multi_ids:
            sub_switches = grouped_switches[real_did]
            # 排序子开关
            sub_switches.sort(key=lambda d: int(str(d.get("did", "")).split(".s")[-1]) if ".s" in str(d.get("did", "")) else 0)
            
            # 使用第一个子设备的信息作为主卡片信息
            main_device = sub_switches[0]
            # 名字通常是 "X键开关"，提取公共部分
            card_name = main_device["name"].split("-")[0] + "开关"
            if "键" in main_device["name"]:
                 # 尝试提取 "中键-H+单火三键开关" -> "H+单火三键开关"
                 parts = main_device["name"].split("-")
                 if len(parts) > 1:
                     card_name = parts[-1] 
            
            switches_list = []
            for sw in sub_switches:
                name = sw.get("name", "开关")
                # 简化名称
                short_name = name.replace("-H+单火", "").replace("开关", "").strip()
                if not short_name: short_name = name
                switches_list.append({
                    "id": sw.get("id"),
                    "name": short_name,
                    "is_on": sw.get("is_on", False)
                })
            
            # 缓存构造数据，供创建使用
            multi_card_data[real_did] = {
                "name": card_name,
                "icon": main_device.get("icon", "🔌"),
                "color": main_device.get("color", "#4CAF50"),
                "switches": switches_list,
                "online": main_device.get("online", False)
            }
            
            if real_did not in self._multi_switch_cards:
                # Create
                card = MultiSwitchCard(
                    self.grid_frame,
                    device_id=real_did,
                    device_name=card_name,
                    switches=switches_list,
                    device_icon=multi_card_data[real_did]["icon"],
                    device_color=multi_card_data[real_did]["color"],
                    is_online=main_device.get("online", False),
                    on_click=on_switch_click,
                    on_long_press=self._on_device_menu
                )
                self._multi_switch_cards[real_did] = card

        # 4. Update All Cards (数据更新)
        # 普通设备
        for device in regular_devices:
            card = self._device_cards[device["id"]]
            card.update_status(
                is_online=device.get("online", False),
                status_text=device.get("status_text", "离线"),
                is_on=device.get("is_on", False)
            )
            
        # 多键开关
        for real_did in target_multi_ids:
            card = self._multi_switch_cards[real_did]
            data = multi_card_data[real_did]
            # 更新在线状态
            card.update_online_status(data["online"])
            # 更新子开关状态
            for sw in data["switches"]:
                card.update_switch_state(sw["id"], sw["is_on"])

        # 5. Grid Layout (重新布局)
        row, col = 0, 0
        MAX_COLS = 4
        
        # 布局多键开关
        for real_did in target_multi_ids:
            card = self._multi_switch_cards[real_did]
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.tkraise()
            
            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1
                
        # 布局普通设备
        for device in regular_devices:
            card = self._device_cards[device["id"]]
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.tkraise()
            
            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1
                
        # 布局添加按钮
        if not hasattr(self, '_add_device_card') or not self._add_device_card.winfo_exists():
            self._add_device_card = AddDeviceCard(
                self.grid_frame,
                on_click=self._on_add_device
            )
        
        self._add_device_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        self._add_device_card.tkraise()
        
        t_end = time.time()
        print(f"[UI Monitor] DeviceGrid SMART REFLOW: {(t_end - t_start)*1000:.1f}ms (Regular: {len(regular_devices)}, Multi: {len(grouped_switches)})")
    
    def update_device(self, device_id: str, is_online: bool, status_text: str, is_on: bool = False) -> None:
        if device_id in self._device_cards:
            self._device_cards[device_id].update_status(is_online, status_text, is_on)
    
    def update_switch_state(self, switch_id: str, is_on: bool, is_online: bool = True) -> None:
        """更新多键开关中某个按键的状态"""
        if hasattr(self, '_multi_switch_cards'):
            for card in self._multi_switch_cards.values():
                if switch_id in card.get_switch_ids():
                    # 同时更新在线状态和开关状态
                    card.update_online_status(is_online)
                    card.update_switch_state(switch_id, is_on)
                    break
    
    def get_device_ids(self) -> List[str]:
        return list(self._device_cards.keys())

    def _create_status_item(self, key, icon, text):
        container = ctk.CTkFrame(self.status_row, fg_color="transparent")
        container.pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(
            container,
            text=icon,
            font=(Theme.FONT_EMOJI, 14),
            text_color=Theme.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 4))
        
        label = ctk.CTkLabel(
            container,
            text=text,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            text_color=Theme.TEXT_SECONDARY
        )
        label.pack(side="left")
        self._status_widgets[key] = label

    def update_header_status(self, temp=None, hum=None, pm25=None):
        """更新顶部状态栏数据"""
        if temp is not None:
            self._status_widgets["temp"].configure(text=f"{temp}°C")
        if hum is not None:
            self._status_widgets["hum"].configure(text=f"{hum}%")
        if pm25 is not None:
             self._status_widgets["air"].configure(text=f"{pm25} μg/m³")

