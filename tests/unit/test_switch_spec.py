"""
测试脚本：查询设备 MIoT Spec 并测试控制
"""
import sys
sys.path.insert(0, ".")
from mijiaAPI import mijiaAPI

# 初始化 API
api = mijiaAPI(".mijia-api-data/auth.json")

if not api.available:
    print("请先登录！")
    api.login()

# 获取设备列表
print("\n===== 设备列表 =====")
devices = api.get_devices_list()
for d in devices:
    model = d.get("model", "")
    if "switch" in model.lower() or "huca" in model.lower():
        print(f"名称: {d.get('name')}")
        print(f"  DID: {d.get('did')}")
        print(f"  Model: {model}")
        print(f"  isOnline: {d.get('isOnline')}")
        print()

# 查询三键开关 spec
print("\n===== 三键开关 (1080650797) 属性查询 =====")
try:
    device = api.get_device("1080650797")
    print(f"设备属性列表: {device.prop_list if hasattr(device, 'prop_list') else '不可用'}")
    
    # 测试读取各个 siid 的 on 状态
    for siid in range(2, 7):
        try:
            result = api.get_devices_prop({
                "did": "1080650797",
                "siid": siid,
                "piid": 1
            })
            print(f"siid={siid}, piid=1: {result}")
        except Exception as e:
            print(f"siid={siid}, piid=1: 错误 - {e}")
except Exception as e:
    print(f"查询失败: {e}")

# 查询双键开关 spec
print("\n===== 双键开关 (1081846216) 属性查询 =====")
try:
    for siid in range(2, 6):
        try:
            result = api.get_devices_prop({
                "did": "1081846216",
                "siid": siid,
                "piid": 1
            })
            print(f"siid={siid}, piid=1: {result}")
        except Exception as e:
            print(f"siid={siid}, piid=1: 错误 - {e}")
except Exception as e:
    print(f"查询失败: {e}")

print("\n===== 测试控制三键开关 =====")
print("输入 siid 和 value (例如: 2 True 或 3 False):")
user_input = input("> ")
if user_input:
    parts = user_input.split()
    if len(parts) == 2:
        siid = int(parts[0])
        value = parts[1].lower() == "true"
        print(f"设置 siid={siid}, piid=1, value={value}")
        result = api.set_devices_prop({
            "did": "1080650797",
            "siid": siid,
            "piid": 1,
            "value": value
        })
        print(f"结果: {result}")
