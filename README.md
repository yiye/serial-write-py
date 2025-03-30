# Serial Write Python

一个用于与ESP32设备通信的Python脚本，可以通过串口发送系统信息数据。

## 功能特性

- 自动检测并连接到指定序列号的ESP32设备
- 收集并发送系统信息，包括：
  - 网络连接信息（WiFi、以太网）的IP和MAC地址
  - 操作系统平台信息
  - CPU和内存使用率
  - 当前日期和时间
- 使用STX/ETX协议帧发送JSON格式数据
- 定期（每30秒）自动更新系统信息
- 接收并显示ESP32的响应消息

## 安装

### 前提条件

- Python 3.7+
- 连接的ESP32设备（序列号为24:58:7C:D3:68:AC）

### 依赖安装

```bash
pip install -r requirements.txt
```

或者使用uv（更快的包管理器）：

```bash
uv pip install -r requirements.txt
```

## 使用方法

运行主脚本即可启动与ESP32的通信：

```bash
python main.py
```

脚本将执行以下步骤：
1. 扫描并查找目标ESP32设备
2. 建立串口连接（波特率115200）
3. 发送系统信息JSON数据
4. 监听ESP32响应
5. 每30秒自动更新并发送系统信息

## 数据格式

发送到ESP32的JSON数据格式示例：

```json
{
  "network": {
    "WiFi": {
      "mac": "XX:XX:XX:XX:XX:XX",
      "ip": "192.168.1.100"
    },
    "Ethernet": {
      "mac": "XX:XX:XX:XX:XX:XX",
      "ip": "192.168.1.101"
    }
  },
  "platform": "Windows-10",
  "cpu_percent": 25.5,
  "memory_percent": 60.2,
  "time": "15:30",
  "date": "Monday, 01"
}
```

## 项目结构

- `main.py` - 主程序文件，包含所有功能
- `requirements.txt` - 项目依赖列表
- `.python-version` - Python版本控制文件
- `pyproject.toml`和`uv.lock` - 项目配置文件

## 依赖库

- pyserial - 用于串口通信
- netifaces - 用于获取网络接口信息
- psutil - 用于系统资源监控
- platform, datetime, json - Python标准库

## 协议

JSON数据使用STX/ETX协议帧进行传输：
- 0x02 (STX) - 数据帧开始
- JSON数据（分块传输，每块最大32字节）
- 换行符
- 0x03 (ETX) - 数据帧结束
