"""
AquaGuard 韩家家庭智能系统 - 仪表盘模块

显示传感器数据：水温、TDS、水位
"""

import customtkinter as ctk
from typing import Optional
import math


class TemperatureGauge(ctk.CTkFrame):
    """水温仪表盘 - 带动态效果的圆形温度显示"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="#16213e", corner_radius=15)
        
        # 标题
        self.title_label = ctk.CTkLabel(
            self,
            text="🌡️ 水温",
            font=("微软雅黑", 14, "bold"),
            text_color="#00e5ff"
        )
        self.title_label.pack(pady=(15, 5))
        
        # 温度画布
        self.canvas = ctk.CTkCanvas(
            self,
            width=150,
            height=150,
            bg="#16213e",
            highlightthickness=0
        )
        self.canvas.pack(pady=10)
        
        # 温度值
        self.temp_label = ctk.CTkLabel(
            self,
            text="--.-°C",
            font=("Roboto", 28, "bold"),
            text_color="#ffffff"
        )
        self.temp_label.pack(pady=(0, 5))
        
        # 状态标签
        self.status_label = ctk.CTkLabel(
            self,
            text="等待连接...",
            font=("微软雅黑", 11),
            text_color="#888888"
        )
        self.status_label.pack(pady=(0, 15))
        
        # 当前温度
        self._temperature = 0.0
        self._animation_angle = 0
        
        # 绘制初始状态
        self._draw_gauge()
    
    def set_temperature(self, temp: float) -> None:
        """设置温度值"""
        self._temperature = temp
        self.temp_label.configure(text=f"{temp:.1f}°C")
        
        # 根据温度设置颜色和状态
        if temp < 18:
            color = "#00bcd4"  # 冷 - 青色
            status = "温度偏低"
        elif temp < 22:
            color = "#4caf50"  # 正常偏低 - 绿色
            status = "温度正常"
        elif temp <= 28:
            color = "#4caf50"  # 正常 - 绿色
            status = "温度适宜"
        elif temp <= 30:
            color = "#ff9800"  # 偏高 - 橙色
            status = "温度偏高"
        else:
            color = "#ff2e63"  # 过高 - 红色
            status = "温度危险！"
        
        self.temp_label.configure(text_color=color)
        self.status_label.configure(text=status, text_color=color)
        self._draw_gauge(color)
    
    def _draw_gauge(self, color: str = "#00e5ff") -> None:
        """绘制仪表盘"""
        self.canvas.delete("all")
        
        cx, cy = 75, 75
        radius = 60
        
        # 背景圆环
        self.canvas.create_oval(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            outline="#2a3f5f",
            width=8
        )
        
        # 模拟水波纹效果（多层同心圆）
        for i in range(3):
            r = radius - 15 - i * 10
            alpha = 0.3 - i * 0.1
            self.canvas.create_oval(
                cx - r, cy - r,
                cx + r, cy + r,
                outline=color,
                width=2,
                stipple="gray50" if i > 0 else ""
            )
        
        # 中心温度区域
        self.canvas.create_oval(
            cx - 25, cy - 25,
            cx + 25, cy + 25,
            fill=color,
            outline=""
        )


class TDSMeter(ctk.CTkFrame):
    """TDS 纯净度条"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="#16213e", corner_radius=15)
        
        # 标题
        self.title_label = ctk.CTkLabel(
            self,
            text="💧 水质 (TDS)",
            font=("微软雅黑", 14, "bold"),
            text_color="#00e5ff"
        )
        self.title_label.pack(pady=(15, 10))
        
        # TDS 值
        self.value_label = ctk.CTkLabel(
            self,
            text="--- ppm",
            font=("Roboto", 24, "bold"),
            text_color="#ffffff"
        )
        self.value_label.pack(pady=5)
        
        # 进度条容器
        self.bar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bar_frame.pack(fill="x", padx=20, pady=10)
        
        # 进度条
        self.progress_bar = ctk.CTkProgressBar(
            self.bar_frame,
            orientation="horizontal",
            height=20,
            corner_radius=10,
            progress_color="#4caf50"
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        
        # 刻度标签
        self.scale_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.scale_frame.pack(fill="x", padx=20)
        
        for text, anchor in [("0", "w"), ("150", "center"), ("300+", "e")]:
            label = ctk.CTkLabel(
                self.scale_frame,
                text=text,
                font=("微软雅黑", 9),
                text_color="#666666"
            )
            if anchor == "w":
                label.pack(side="left")
            elif anchor == "e":
                label.pack(side="right")
            else:
                label.pack(expand=True)
        
        # 等级标签
        self.grade_label = ctk.CTkLabel(
            self,
            text="等级: --",
            font=("微软雅黑", 12),
            text_color="#888888"
        )
        self.grade_label.pack(pady=(5, 15))
    
    def set_tds(self, tds: int) -> None:
        """设置 TDS 值"""
        self.value_label.configure(text=f"{tds} ppm")
        
        # 计算进度（0-300 映射到 0-1）
        progress = min(1.0, tds / 300)
        self.progress_bar.set(progress)
        
        # 根据 TDS 设置颜色和等级
        if tds < 150:
            color = "#4caf50"  # 优 - 绿色
            grade = "优"
        elif tds < 300:
            color = "#ff9800"  # 良 - 橙色
            grade = "良"
        else:
            color = "#ff2e63"  # 差 - 红色
            grade = "差"
        
        self.progress_bar.configure(progress_color=color)
        self.value_label.configure(text_color=color)
        self.grade_label.configure(text=f"等级: {grade}", text_color=color)


class WaterLevelIndicator(ctk.CTkFrame):
    """水位状态指示灯"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="#16213e", corner_radius=15)
        
        # 标题
        self.title_label = ctk.CTkLabel(
            self,
            text="🚰 水位",
            font=("微软雅黑", 14, "bold"),
            text_color="#00e5ff"
        )
        self.title_label.pack(pady=(15, 10))
        
        # 水滴图标画布
        self.canvas = ctk.CTkCanvas(
            self,
            width=80,
            height=100,
            bg="#16213e",
            highlightthickness=0
        )
        self.canvas.pack(pady=10)
        
        # 状态标签
        self.status_label = ctk.CTkLabel(
            self,
            text="等待连接...",
            font=("微软雅黑", 14, "bold"),
            text_color="#888888"
        )
        self.status_label.pack(pady=(0, 15))
        
        self._draw_droplet(normal=True)
    
    def set_water_level(self, level: int) -> None:
        """设置水位状态（1=正常, 0=缺水）"""
        normal = level == 1
        self._draw_droplet(normal)
        
        if normal:
            self.status_label.configure(text="水位正常", text_color="#00e5ff")
        else:
            self.status_label.configure(text="水位过低！", text_color="#ff2e63")
    
    def _draw_droplet(self, normal: bool) -> None:
        """绘制水滴图标"""
        self.canvas.delete("all")
        
        cx, cy = 40, 55
        color = "#00e5ff" if normal else "#ff2e63"
        
        # 绘制水滴形状
        points = []
        for i in range(100):
            angle = i * 2 * math.pi / 100
            if i < 50:
                # 上半部分 - 尖角
                r = 25 * (1 - abs(angle - math.pi/2) / (math.pi/2))
                x = cx + r * math.cos(angle)
                y = cy - 30 + r * math.sin(angle)
            else:
                # 下半部分 - 圆形
                r = 25
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle) * 0.8
            points.extend([x, y])
        
        # 简化的水滴
        self.canvas.create_oval(
            cx - 25, cy - 10,
            cx + 25, cy + 40,
            fill=color,
            outline=""
        )
        self.canvas.create_polygon(
            cx, cy - 35,
            cx - 20, cy,
            cx + 20, cy,
            fill=color,
            outline=""
        )
        
        # 缺水时添加划线
        if not normal:
            self.canvas.create_line(
                cx - 30, cy + 50,
                cx + 30, cy - 30,
                fill="#ff2e63",
                width=4
            )


class DashboardPanel(ctk.CTkFrame):
    """仪表盘面板"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="transparent")
        
        # 标题
        title = ctk.CTkLabel(
            self,
            text="📊 实时监测仪表盘",
            font=("微软雅黑", 20, "bold"),
            text_color="#00e5ff"
        )
        title.pack(pady=(0, 20))
        
        # 连接状态
        self.status_frame = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=10)
        self.status_frame.pack(fill="x", pady=(0, 20))
        
        self.connection_label = ctk.CTkLabel(
            self.status_frame,
            text="⚪ 传感器节点: 未连接",
            font=("微软雅黑", 12),
            text_color="#888888"
        )
        self.connection_label.pack(side="left", padx=15, pady=10)
        
        self.wifi_label = ctk.CTkLabel(
            self.status_frame,
            text="信号: --",
            font=("微软雅黑", 12),
            text_color="#888888"
        )
        self.wifi_label.pack(side="right", padx=15, pady=10)
        
        # 仪表容器
        self.gauges_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.gauges_frame.pack(fill="both", expand=True)
        
        # 配置网格
        self.gauges_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.gauges_frame.grid_rowconfigure(0, weight=1)
        
        # 水温仪表
        self.temp_gauge = TemperatureGauge(self.gauges_frame)
        self.temp_gauge.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # TDS 显示
        self.tds_meter = TDSMeter(self.gauges_frame)
        self.tds_meter.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # 水位指示
        self.water_indicator = WaterLevelIndicator(self.gauges_frame)
        self.water_indicator.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
    
    def update_sensor_data(self, temperature: float, tds: int, water_level: int,
                          connected: bool, wifi_signal: int = 0) -> None:
        """更新传感器数据"""
        self.temp_gauge.set_temperature(temperature)
        self.tds_meter.set_tds(tds)
        self.water_indicator.set_water_level(water_level)
        
        if connected:
            self.connection_label.configure(
                text="🟢 传感器节点: 已连接",
                text_color="#4caf50"
            )
            self.wifi_label.configure(
                text=f"信号: {wifi_signal} dBm",
                text_color="#888888"
            )
        else:
            self.connection_label.configure(
                text="🔴 传感器节点: 未连接",
                text_color="#ff2e63"
            )
            self.wifi_label.configure(text="信号: --")
    
    def set_disconnected(self) -> None:
        """设置为断开状态"""
        self.connection_label.configure(
            text="🔴 传感器节点: 未连接",
            text_color="#ff2e63"
        )
        self.wifi_label.configure(text="信号: --", text_color="#888888")
