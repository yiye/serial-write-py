import serial
import serial.tools.list_ports
import time

def list_available_ports():
    """列出所有可用的串口设备"""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("没有找到可用的串口设备！")
        return None
    
    print("\n可用的串口设备：")
    for i, port in enumerate(ports, 1):
        print(f"{i}. {port.device} - {port.description}")
    
    return ports

def select_port(ports):
    """让用户选择要连接的串口设备"""
    while True:
        try:
            choice = int(input("\n请选择要连接的设备编号 (输入数字): "))
            if 1 <= choice <= len(ports):
                return ports[choice - 1].device
            else:
                print("无效的选择，请重试！")
        except ValueError:
            print("请输入有效的数字！")

def main():
    # 列出可用设备
    ports = list_available_ports()
    if not ports:
        return

    # 选择设备
    selected_port = select_port(ports)
    
    try:
        # 打开串口连接
        ser = serial.Serial(
            port=selected_port,
            baudrate=115200,  # 默认波特率，可以根据需要修改
            timeout=1
        )
        print(f"\n成功连接到 {selected_port}")
        
        # 等待用户输入并发送
        print("\n开始发送数据 (输入 'quit' 退出):")
        while True:
            user_input = input("请输入要发送的数据: ")
            if user_input.lower() == 'quit':
                break
            
            # 发送数据
            ser.write(user_input.encode())
            print(f"已发送: {user_input}")
            
            # 等待一小段时间确保数据发送完成
            time.sleep(0.1)
            
    except serial.SerialException as e:
        print(f"串口通信错误: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("\n串口连接已关闭")

if __name__ == "__main__":
    main() 