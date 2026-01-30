"""
AquaGuard 鱼缸管理系统 - 硬件节点集成界面
对应文档: AquaGuard 鱼缸管理系统 - 硬件节点集成文档 (ESP32)
"""

import customtkinter as ctk
import requests
import threading
import time
from typing import Callable, Optional
from .theme import Theme

class StatusCard(ctk.CTkFrame):
    pass

class ControlCard(ctk.CTkFrame):
    pass

class AutomationPanel(ctk.CTkFrame):
    """
    鱼缸系统界面 (原自动化中心)
    集成 ESP32 硬件节点控制与状态显示
    """

    def __init__(self, master, **kwargs):
        super().__init__(master)
        self.configure(fg_color="transparent")

        # 兼容性参数处理 (保留 app.py 调用接口)
        self.on_alert_settings_change = kwargs.get("on_alert_settings_change")
        self.on_schedule_change = kwargs.get("on_schedule_change")

        # 获取配置
        from core.config import get_config
        self.config = get_config()
        self.ip_address = self.config.get_fish_tank_ip()
        self.polling = True # 默认开启轮询

        # UI 布局
        self._create_ui()

        # 启动自动连接
        self.after(1000, self._start_polling)

    def _start_polling(self):
        """启动轮询"""
        if self.polling:
            threading.Thread(target=self._poll_loop, daemon=True).start()

    def _create_ui(self):
        # 顶部标题栏
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(30, 20))

        # 标题与状态指示
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        # 右侧状态：最后更新时间 + 简易状态灯
        status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        status_frame.pack(side="right", padx=10)

        self.last_update_label = ctk.CTkLabel(
            status_frame,
            text="等待数据...",
            font=("Consolas", 12),
            text_color=Theme.TEXT_MUTED
        )
        self.last_update_label.pack(side="left", padx=(0, 10))

        # 状态指示灯 (仅显示颜色点，不显示文字)
        self.status_dot = ctk.CTkLabel(
            status_frame,
            text="●",
            font=("Arial", 24),
            text_color=Theme.TEXT_MUTED
        )
        self.status_dot.pack(side="left")

        # 主要内容区域 (网格布局)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=25, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=3) # 左侧信息区更宽
        self.content_frame.grid_columnconfigure(1, weight=2) # 右侧控制区

        # === 左侧：传感器数据 ===
        left_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        # 1. 水温大卡片
        self.temp_card = ctk.CTkFrame(left_panel, fg_color=Theme.BG_CARD, corner_radius=Theme.CORNER_RADIUS)
        self.temp_card.pack(fill="x", pady=(0, 15))

        temp_header = ctk.CTkFrame(self.temp_card, fg_color="transparent")
        temp_header.pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(temp_header, text="🌡️ 实时水温", font=(Theme.FONT_FAMILY, 16, "bold"), text_color=Theme.TEXT_SECONDARY).pack(side="left")

        self.temp_value = ctk.CTkLabel(self.temp_card, text="--", font=("Impact", 64), text_color=Theme.ACCENT_PRIMARY)
        self.temp_value.pack(pady=(0, 10))
        ctk.CTkLabel(self.temp_card, text="°C", font=(Theme.FONT_FAMILY, 20, "bold"), text_color=Theme.TEXT_MUTED).place(relx=0.75, rely=0.55)

        # 2. 水位监测卡片
        self.water_card = ctk.CTkFrame(left_panel, fg_color=Theme.BG_CARD, corner_radius=Theme.CORNER_RADIUS)
        self.water_card.pack(fill="x")

        water_header = ctk.CTkFrame(self.water_card, fg_color="transparent")
        water_header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(water_header, text="🌊 水位监测", font=(Theme.FONT_FAMILY, 16, "bold"), text_color=Theme.TEXT_SECONDARY).pack(side="left")

        self.water_status_bar = ctk.CTkProgressBar(self.water_card, height=15, corner_radius=8)
        self.water_status_bar.pack(fill="x", padx=25, pady=(10, 5))
        self.water_status_bar.set(0) # 初始0

        self.water_text = ctk.CTkLabel(self.water_card, text="检测中...", font=(Theme.FONT_FAMILY, 18, "bold"), text_color=Theme.TEXT_MUTED)
        self.water_text.pack(pady=(0, 20))

        # === 右侧：控制与日志 ===
        right_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew")

        # 1. 灯光控制面板
        control_group = ctk.CTkFrame(right_panel, fg_color=Theme.BG_CARD, corner_radius=Theme.CORNER_RADIUS)
        control_group.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(control_group, text="💡 氛围灯光", font=(Theme.FONT_FAMILY, 16, "bold"), text_color=Theme.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(20, 15))

        btn_container = ctk.CTkFrame(control_group, fg_color="transparent")
        btn_container.pack(fill="x", padx=20, pady=(0, 25))

        self.on_btn = ctk.CTkButton(
            btn_container,
            text="开启照明",
            command=lambda: self._control_light("on"),
            height=45,
            font=(Theme.FONT_FAMILY, 14, "bold"),
            fg_color=Theme.BG_SECONDARY,
            text_color=Theme.TEXT_PRIMARY,
            hover_color=Theme.ACCENT_PRIMARY
        )
        self.on_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.off_btn = ctk.CTkButton(
            btn_container,
            text="关闭",
            command=lambda: self._control_light("off"),
            height=45,
            font=(Theme.FONT_FAMILY, 14, "bold"),
            fg_color=Theme.BG_SECONDARY,
            text_color=Theme.TEXT_PRIMARY,
            hover_color=Theme.ACCENT_ERROR
        )
        self.off_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # 2. 系统日志终端
        log_group = ctk.CTkFrame(right_panel, fg_color=Theme.BG_CARD, corner_radius=Theme.CORNER_RADIUS)
        log_group.pack(fill="both", expand=True)

        log_header = ctk.CTkFrame(log_group, fg_color="transparent")
        log_header.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(log_header, text="📟 节点数据流", font=(Theme.FONT_FAMILY, 13, "bold"), text_color=Theme.TEXT_MUTED).pack(side="left")

        # 刷新IP提示
        self.ip_label = ctk.CTkLabel(log_header, text=f"IP: {self.ip_address}", font=("Consolas", 10), text_color=Theme.TEXT_MUTED)
        self.ip_label.pack(side="right")

        self.log_text = ctk.CTkTextbox(log_group, font=("Consolas", 11), fg_color=Theme.BG_PRIMARY, text_color="#A0A0A0", corner_radius=8)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _toggle_polling(self):
        # 此方法不再通过按钮触发，保留兼容性
        pass

    def _poll_loop(self):
        while self.polling:
            # 动态获取最新配置的IP
            self.ip_address = self.config.get_fish_tank_ip()

            # 更新UI上的IP显示
            try:
                self.after(0, lambda: self.ip_label.configure(text=f"IP: {self.ip_address}"))
            except:
                pass

            try:
                url = f"http://{self.ip_address}/status"
                resp = requests.get(url, timeout=2)
                data = resp.json()

                self.after(0, lambda d=data: self._update_ui(d))
                self.after(0, self._set_online)

            except Exception as e:
                self.after(0, lambda err=str(e): self._log_error(err))
                self.after(0, self._set_offline)

            time.sleep(3)

    def _set_online(self):
        self.status_dot.configure(text_color=Theme.ACCENT_PRIMARY) # 绿色
        # 更新最后刷新时间
        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.last_update_label.configure(text=f"Last Update: {now}", text_color=Theme.TEXT_SECONDARY)

    def _set_offline(self):
        self.status_dot.configure(text_color=Theme.ACCENT_ERROR) # 红色
        self.last_update_label.configure(text="连接中断", text_color=Theme.ACCENT_ERROR)

    def _update_ui(self, data):
        # 格式化日志
        import json
        pretty_json = json.dumps(data, indent=2, ensure_ascii=False)
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", pretty_json)

        # 更新水温
        temp = data.get("temperature", 0)
        self.temp_value.configure(text=f"{temp:.1f}")

        # 更新水位
        wl = data.get("water_level", 0)
        if wl == 1:
            self.water_text.configure(text="水位正常", text_color=Theme.ACCENT_PRIMARY)
            self.water_status_bar.configure(progress_color=Theme.ACCENT_PRIMARY)
            self.water_status_bar.set(1.0)
        else:
            self.water_text.configure(text="⚠️ 缺水警报", text_color=Theme.ACCENT_ERROR)
            self.water_status_bar.configure(progress_color=Theme.ACCENT_ERROR)
            self.water_status_bar.set(0.2) # 显示一点点红色

        # 更新灯光按钮状态
        power = data.get("power", "off")
        if power == "on":
            self.on_btn.configure(fg_color=Theme.ACCENT_PRIMARY, text="照明已开启")
            self.off_btn.configure(fg_color=Theme.BG_SECONDARY, text="关闭")
        else:
            self.on_btn.configure(fg_color=Theme.BG_SECONDARY, text="开启照明")
            self.off_btn.configure(fg_color=Theme.ACCENT_ERROR, text="已关闭")

    def _control_light(self, action):
        url = f"http://{self.ip_address}/{action}"
        def run():
            try:
                requests.get(url, timeout=2)
                # 触发手动刷新
                threading.Thread(target=self._manual_refresh, daemon=True).start()
            except Exception as e:
                self.after(0, lambda: self._log_error(f"控制失败: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def _manual_refresh(self):
        try:
            url = f"http://{self.ip_address}/status"
            resp = requests.get(url, timeout=2)
            self.after(0, lambda: self._update_ui(resp.json()))
        except:
            pass

    def _log_error(self, msg):
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", f"Connection Error: {msg}\nCheck IP: {self.ip_address}")

    # ================= 兼容性接口 =================

    def set_initial_values(self, *args, **kwargs):
        pass

    def add_alert(self, message: str):
        # 将报警信息显示在日志中
        self.log_text.insert("end", f"\n[System Alert] {message}")

    def set_alert_logs(self, logs: list):
        pass

    def set_clear_callback(self, callback: Callable):
        pass
