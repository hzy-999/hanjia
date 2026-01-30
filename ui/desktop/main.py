"""
AquaGuard 韩家家庭智能系统 - 主程序入口
"""

import sys
import os

# 将 desktop 目录添加到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import run_app

if __name__ == "__main__":
    print("=" * 50)
    print("🐠 AquaGuard 韩家家庭智能系统")
    print("=" * 50)
    print("正在启动桌面应用...")
    print()
    
    run_app()
