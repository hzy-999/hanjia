# 米家设备数据映射文档 (Device Data Mapping)

本文档记录了系统中使用的主要米家设备的数据映射关系，特别是多键开关和智能插座的控制指令映射（SIID/PIID）。

## 1. H+ 单火三键开关 (H+ Single Fire Three-Key Switch)

*   **型号 (Model)**: `huca.switch.dh3`
*   **Spec Type**: `urn:miot-spec-v2:device:switch:0000A003:huca-dh3:1:0000C810`
*   **说明**: 该设备包含三个独立的开关按键。在系统中，通过虚拟 DID 后缀 `.sX` 来区分不同按键。

| 按键名称 | 虚拟 DID 后缀 | SIID (Service ID) | PIID (Property ID) | 属性 (Property) | 值 (Value) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **左键** (Left) | `.s2` | `2` | `1` | On (开关) | true/false |
| **中键** (Center) | `.s3` | `3` | `1` | On (开关) | true/false |
| **右键** (Right) | `.s4` | `4` | `1` | On (开关) | true/false |

**示例控制指令**:
*   打开左键: `Set Property { did: "real_did", siid: 2, piid: 1, value: true }`

## 2. H+ 单火双键开关 (H+ Single Fire Double-Key Switch)

*   **型号 (Model)**: `huca.switch.dh2`
*   **Spec Type**: `urn:miot-spec-v2:device:switch:0000A003:huca-dh2:1:0000C809`
*   **说明**: 该设备包含两个独立的开关按键。

| 按键名称 | 虚拟 DID 后缀 | SIID (Service ID) | PIID (Property ID) | 属性 (Property) | 值 (Value) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **左键** (Left) | `.s2` | `2` | `1` | On (开关) | true/false |
| **右键** (Right) | `.s3` | `3` | `1` | On (开关) | true/false |

**注意**: 若存在 `s1` 或其他后缀，通常对应主设备或特定组合，但在当前系统中主要使用 `s2` 和 `s3` 分别控制两路。

## 3. 智能插座/开关 (Smart Switch/Socket)

此类设备在米家中通常被识别为单路插座或开关。

*   **型号 (Model)**: `iot.plug.socn1`
*   **Spec Type**: `urn:miot-spec-v2:device:outlet:0000A002:iot-socn1:2`
*   **涉及设备**:
    *   **大鱼缸灯** (Fish Tank Light)
    *   **乌龟晒背** (Turtle Back Sun)
    *   **电脑 智能插座P1**

| 功能 | SIID (Service ID) | PIID (Property ID) | 属性 (Property) | 值 (Value) |
| :--- | :--- | :--- | :--- | :--- |
| **电源开关** | `2` (Outlet) | `1` (On) | On (开关) | true/false |

**说明**:
*   虽然名称可能是"灯"或"乌龟晒背"，但在米家协议中它们均作为标准的**智能插座 (Outlet)** 进行控制。
*   控制指令统一为: `siid=2, piid=1`。

## 4. 映射逻辑说明 (MijiaAdapter)

当前系统的 `MijiaAdapter` (`mijia_adapter.py`) 使用以下逻辑解析虚拟 DID：

```python
# 虚拟 DID 格式: real_did.sN
parts = did.split(".")
real_did = parts[0]
idx = int(parts[1].replace("s", ""))

# 映射规则:
# SIID = idx (例如 .s2 -> siid=2)
# PIID = 1 (固定为 1，对应 On 属性)
```

若需扩展支持其他属性（如色温、亮度），需修改 `_get_virtual_prop` 和 `_set_virtual_prop` 方法中的 PIID 映射逻辑。
