"""
AquaGuard UI 主题配置

风格: Glassmorphism / Henry's Home Style
特点: 仿毛玻璃、大圆角、淡蓝渐变背景模拟、Material 配色
参考: 用户 HTML 代码
"""

class Theme:
    # 背景色 (Premium Light - 苹果/Material 3 风格)
    BG_PRIMARY = "#F8FAFC"    # Slate 50 (主背景，极淡灰蓝)
    BG_SECONDARY = "#F1F5F9"  # Slate 100 (次级背景)
    
    # 卡片颜色 (Card Surface)
    BG_CARD = "#FFFFFF"       # White (纯白卡片)
    BG_CARD_HOVER = "#FDFDFD"  # 微妙的悬停变化
    
    # 文字颜色 (Modern Typography)
    TEXT_PRIMARY = "#0F172A"   # Slate 900 (黑)
    TEXT_SECONDARY = "#475569" # Slate 600 (中灰)
    TEXT_MUTED = "#94A3B8"     # Slate 400 (淡灰)
    
    # 强调色 (Sophisticated Indigo - 高级科技感)
    ACCENT_PRIMARY = "#6366F1"   # Indigo 500 (主色)
    ACCENT_HOVER = "#818CF8"     # Indigo 400
    
    # 场景/状态色 (Soft Pastel - 适配高档感)
    COLOR_SUNNY = "#F59E0B"      # Amber 500
    COLOR_BLUE = "#38BDF8"       # Sky 400
    COLOR_INDIGO = "#818CF8"     # Indigo 400
    COLOR_PURPLE = "#A855F7"     # Purple 500
    
    # 状态色
    ACCENT_SUCCESS = "#10B981"   # Emerald 500
    ACCENT_WARNING = "#F59E0B"   # Amber 500
    ACCENT_ERROR = "#EF4444"     # Red 500
    
    # 边框与阴影模拟 (Refined)
    BORDER_DEFAULT = "#E2E8F0"    # Slate 200 (极细边框)
    BORDER_ACTIVE = "#6366F1"     # Active Indigo
    
    # 字体
    FONT_FAMILY = "Microsoft YaHei UI"
    FONT_EMOJI = "Segoe UI Emoji"
    
    # 圆角 (Apple 风格大圆角)
    CORNER_RADIUS = 24  # 更高级的大圆角
    BUTTON_RADIUS = 12  # 按钮保持灵动
