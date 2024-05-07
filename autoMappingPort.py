import json
import os
import time

import requests
import yaml

from utils import get_adb_devices

# 假设openDoorURL是一个API端点，可以打开hub端口
openDoorURL = "http://127.0.0.1:8200/hub/openDoorOnly"

# 要遍历的端口范围
start_port = 1
end_port = 20

# 用于存储端口与设备ID映射的YAML文件路径
output_yaml_file = "port_device_mapping.yaml"
# 删除文件
if os.path.exists(output_yaml_file):  # 先检查文件是否存在，避免错误
    os.remove(output_yaml_file)
    print(f"文件 {output_yaml_file} 已删除。")
else:
    print(f"文件 {output_yaml_file} 不存在。")

# 遍历指定的端口范围
for port in range(start_port, end_port + 1):
    # 录入数组
    json_array = json.dumps([port])
    # 调用openDoorURL接口以打开端口
    response = requests.post(openDoorURL, headers={'Content-Type': 'application/json'},
                              data=json_array)
    time.sleep(10)
    if response.status_code != 200:
        print(f"Failed to open port {port}. Skipping...")
        continue

    # 执行adb device命令并解析输出
    devices = get_adb_devices()
    device_id = None

    # 查找匹配的设备ID
    # fixme 状态无意义
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