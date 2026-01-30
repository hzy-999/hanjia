"""
设备型号检查工具

原文件: inspect_model.py
"""
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mijiaAPI.devices import get_device_info


def inspect_model(model: str):
    """检查设备型号信息"""
    print(f"Fetching info for {model}...")
    try:
        info = get_device_info(model)
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return info
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="检查设备型号信息")
    parser.add_argument("model", nargs="?", default="huca.switch.dh3", help="设备型号")
    args = parser.parse_args()
    inspect_model(args.model)


if __name__ == "__main__":
    main()
