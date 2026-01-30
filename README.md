# mijiaAPI

小米米家设备控制 Python 库，支持 API 调用和命令行工具。

[![PyPI](https://img.shields.io/badge/PyPI-mijiaAPI-blue)](https://pypi.org/project/mijiaAPI/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green.svg)](https://opensource.org/licenses/GPL-3.0)

## 安装

```bash
pip install mijiaAPI
```

## 快速开始

### 登录

```python
from mijiaAPI import mijiaAPI

api = mijiaAPI()
api.login()  # 扫描终端二维码完成登录
```

### 控制设备

```python
from mijiaAPI import mijiaAPI, mijiaDevice

api = mijiaAPI()
api.login()

# 通过设备名称初始化
device = mijiaDevice(api, dev_name="我的台灯")

# 读取/设置属性
print(device.brightness)
device.brightness = 60
device.on = True
```

### 命令行

```bash
mijiaAPI -l                                              # 列出设备
mijiaAPI get --dev_name "台灯" --prop_name "brightness"  # 获取属性
mijiaAPI set --dev_name "台灯" --prop_name "on" --value True  # 设置属性
```

## 文档

- [常见问题 FAQ](docs/FAQ.md)
- [示例代码](examples/)

## 许可证

[GPL-3.0](LICENSE) - 使用本项目的代码需以相同许可证开源。

## 免责声明

本项目仅供学习交流，不得用于商业用途。使用本项目产生的任何后果由用户自行承担。
