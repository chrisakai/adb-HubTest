import json
import logging
import os
import subprocess
import time

import requests
import yaml

from staticTools import getDevicePortMap

# 假设openDoorURL是一个API端点，可以打开hub端口
openDoorURL = "http://127.0.0.1:8200/hub/openDoorOnly"
closeDoorURL = "http://127.0.0.1:8200/hub/closeDoorOnly"

# 要遍历的端口范围
start_port = 1
end_port = 20
count = 0

# 用于存储端口与设备ID映射的YAML文件路径
output_yaml_file = "port_device_mapping.yaml"
# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s , %(levelname)s ,第%(count)s轮, 端口%(port)s, 设备%(deviceID)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='offline_devices.csv',
                    filemode='a')


# 遍历指定的端口范围
def adb_device():
    try:
        # 执行adb devices命令
        result = subprocess.run(['adb', 'devices'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # 获取标准输出
        output = result.stdout
        # 如果adb命令执行成功，则进一步处理输出
        if result.returncode == 0:
            # 移除标题行 ("List of devices attached")
            devices = output.split('\n')[1:-1]
            # 去除每行前面的空白字符并按需求格式化输出
            device = [line.split('\t')[0] for line in devices if line.strip()]
            status = [line.split('\t')[1] for line in devices if line.strip()]
            if "offline" in status:
                device_port_map = getDevicePortMap()
                port = device_port_map.get(device[0])
                # breakpoint()
                logging.error(f"offline",
                             extra={'count': count, 'port': port, 'deviceID': device})
            return device
        else:
            # 如果adb命令执行失败，则打印错误信息
            print(result.stderr.strip())
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

while(True):
    count += 1
    # 删除文件
    if os.path.exists(output_yaml_file):  # 先检查文件是否存在，避免错误
        os.remove(output_yaml_file)
        print(f"文件 {output_yaml_file} 已删除。")
    else:
        print(f"文件 {output_yaml_file} 不存在。")

    for port in range(start_port, end_port + 1):
        # 录入数组
        json_array = json.dumps([port])

        # 关对应HUB，调用接口closeDoorOnly（模拟领取任务后的拔出操作）
        responseClose = requests.post(closeDoorURL, data=json_array,
                                      headers={'Content-Type': 'application/json'})
        # 检查请求是否成功
        if responseClose.status_code != 200:
            print(f"Failed to close port {port}. Skipping...")
            continue

        # 调用openDoorURL接口以打开端口
        responseOpen = requests.post(openDoorURL, headers={'Content-Type': 'application/json'},
                                  data=json_array)
        if responseOpen.status_code != 200:
            print(f"Failed to open port {port}. Skipping...")
            continue

        time.sleep(5)
        # 执行adb device命令并解析输出
        devices = adb_device()
        device_id = None

        # 查找匹配的设备ID
        for device in devices:
            if "unauthorized" not in device:
                device_id = device.split("\t")[0]
                break

        # 将端口与设备ID写入YAML文件
        if device_id:
            mapping = {int(port): str(device_id)}
            with open(output_yaml_file, "a") as f:
                yaml.dump(mapping, f)
            print(f"Port {port} is bound to device {device_id}.")
        else:
            print(f"No device found for port {port}. Skipping...")

