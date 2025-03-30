from serial.tools import list_ports
import serial.win32
import time
import platform
import json
import netifaces
import psutil
from datetime import datetime


def get_network_info():
    """获取网络连接信息，返回JSON格式的IP地址和MAC地址"""
    try:
        network_info = {}
        
        # 获取所有网络接口
        interfaces = netifaces.interfaces()
        
        for interface in interfaces:
            # 获取接口的地址信息
            addrs = netifaces.ifaddresses(interface)
            
            # 获取MAC地址
            mac = None
            if netifaces.AF_LINK in addrs:
                mac = addrs[netifaces.AF_LINK][0]['addr']
            
            # 获取IPv4地址
            ip = None
            if netifaces.AF_INET in addrs:
                ip = addrs[netifaces.AF_INET][0]['addr']
            
            # 根据接口名称映射到所需的网络类型
            interface_name = interface
            if "Wi-Fi" in interface or "wlan" in interface.lower():
                interface_name = "WiFi"
            elif "Ethernet" in interface or "eth" in interface.lower():
                interface_name = "Ethernet"
            elif "Loopback" in interface or "lo" in interface.lower():
                interface_name = "Loopback"
            
            # 只添加有IP地址的接口
            if ip:
                network_info[interface_name] = {
                    'mac': mac or "",
                    'ip': ip
                }
        
        return network_info
    except Exception as e:
        return {"error": str(e)}

def get_system_info():
    """获取系统信息"""
    current_time = datetime.now()
    system_info = {
        'network': get_network_info(),
        'platform': platform.platform(),
        'cpu_percent': round(psutil.cpu_percent(), 1),
        'memory_percent': round(psutil.virtual_memory().percent, 1),
        'time': current_time.strftime("%H:%M"),
        'date': current_time.strftime("%A, %d")
    }
    return system_info


def find_target_device():
    """查找目标设备（序列号为24:58:7C:D3:68:AC的设备）"""
    target_serial = '24:58:7C:D3:68:AC'
    ports = list_ports.comports()
    
    print("\n扫描串口设备...")
    print("-" * 50)
    
    for port in ports:
        print(f"检查设备: {port.device}")
        print(f"序列号: {port.serial_number}")
        print("-" * 50)
        
        if port.serial_number == target_serial:
            print(f"\n找到目标设备！")
            return port.device
    
    print("\n未找到目标设备")
    return None

def handle_serial_connection(port):
    """处理串口连接"""
    try:
        ser = serial.Serial(
            port=port,
            baudrate=115200,
            timeout=1
        )
        print(f"\n已连接到目标设备 {port}")
        
        # 等待1秒后发送系统信息
        print("等待1秒后发送系统信息...")
        time.sleep(1)
        
        def send_message(json_data):
            """发送消息并确保发送完成"""
            # 清空输入缓冲区
            ser.reset_input_buffer()
            
            # 移除可能的控制字符
            json_data = json_data.replace(chr(0x02), "").replace(chr(0x03), "")
            
            print(f"准备发送数据，JSON长度: {len(json_data)} 字节")
            
            # 发送开始标记
            print("发送STX标记...")
            ser.write(chr(0x02).encode())
            ser.flush()
            time.sleep(0.5)  # 给ESP32足够时间处理STX
            
            # 发送JSON数据
            print("发送JSON数据...")
            # 分批发送数据，每次最多发送32字节
            chunk_size = 32  # 减小每个块的大小
            total_chunks = (len(json_data) + chunk_size - 1) // chunk_size
            
            for i in range(0, len(json_data), chunk_size):
                chunk_num = i // chunk_size + 1
                chunk = json_data[i:i+chunk_size]
                print(f"发送块 {chunk_num}/{total_chunks}，长度: {len(chunk)} 字节")
                ser.write(chunk.encode())
                ser.flush()
                time.sleep(0.1)  # 增加每个数据块之间的延迟
            
            print("所有数据块发送完成，等待100ms...")
            time.sleep(0.1)  # 等待所有数据被ESP32接收
            
            # 发送换行和结束标记
            print("发送结束标记...")
            ser.write(("\n" + chr(0x03)).encode())
            ser.flush()
            
            print("消息发送完成，等待ESP32处理...")
            # 增加消息发送后的等待时间，确保ESP32有足够时间处理
            time.sleep(1.0)
        
        # 发送系统信息
        print("正在发送系统信息...")
        system_info = get_system_info()
        # 使用compact格式发送JSON，避免换行
        json_data = json.dumps(system_info, ensure_ascii=False, separators=(',', ':'))
        send_message(json_data)
        
        # 等待并显示设备响应，同时每隔10秒发送一次系统信息
        last_send_time = time.time()
        last_check_time = time.time()
        check_interval = 0.1  # 每0.1秒检查一次响应
        
        while True:
            current_time = time.time()
            
            # 检查是否需要发送系统信息 (每30秒一次)
            if current_time - last_send_time >= 30:
                print("\n发送定期系统信息...")
                system_info = get_system_info()
                json_data = json.dumps(system_info, ensure_ascii=False, separators=(',', ':'))
                send_message(json_data)
                last_send_time = current_time
            
            # 检查是否到了检查响应的时间 (每0.1秒一次)
            if current_time - last_check_time >= check_interval:
                # 检查是否有设备响应
                if ser.in_waiting:
                    try:
                        data = ser.readline().decode().strip()
                        if data:
                            print(f"ESP32响应: {data}")
                            if data.startswith("ERROR:"):
                                print("警告：消息处理失败")
                            elif data.startswith("OK:"):
                                print("消息处理成功")
                    except UnicodeDecodeError as e:
                        print(f"解码响应数据失败: {e}")
                
                last_check_time = current_time
                
            # 小睡一下，避免CPU占用过高
            time.sleep(0.01)
            
    except serial.SerialException as e:
        print(f"串口通信错误: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print(f"\n串口连接 {port} 已关闭")


def main():
    print("开始扫描目标设备...")
    target_port = find_target_device()
    
    if target_port:
        handle_serial_connection(target_port)
    else:
        print("程序退出：未找到目标设备")

if __name__ == "__main__":
    main() 