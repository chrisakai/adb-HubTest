import requests
import subprocess
import yaml

# 假设openDoorURL是一个API端点，可以打开hub端口
openDoorURL = "http://your-api-endpoint/openDoor"

# 要遍历的端口范围
start_port = 1
end_port = 20

# 用于存储端口与设备ID映射的YAML文件路径
output_yaml_file = "port_device_mapping.yaml"

# 遍历指定的端口范围
for port in range(start_port, end_port + 1):
    # 调用openDoorURL接口以打开端口
    response = requests.post(openDoorURL, json={"port": port})
    if response.status_code != 200:
        print(f"Failed to open port {port}. Skipping...")
        continue

    # 执行adb device命令并解析输出
    device_output = subprocess.check_output(["adb", "device"]).decode("utf-8")
    devices = device_output.strip().split("\n")
    device_id = None

    # 查找匹配的设备ID
    for device in devices:
        if "unauthorized" not in device:
            device_id = device.split("\t")[0]
            break

    # 将端口与设备ID写入YAML文件
    if device_id:
        mapping = {str(port): device_id}
        with open(output_yaml_file, "w") as f:
            yaml.dump(mapping, f)
        print(f"Port {port} is bound to device {device_id}.")
    else:
        print(f"No device found for port {port}. Skipping...")