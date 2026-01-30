"""
净化器诊断脚本 - 薄包装器

此脚本现在调用统一的诊断工具。
直接使用: python -m tools.diagnose --type purifier
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.diagnose import diagnose

if __name__ == "__main__":
    diagnose(device_type="purifier")
