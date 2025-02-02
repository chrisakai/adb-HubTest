# -*- coding: utf-8 -*-
import datetime
import hashlib
import logging
import os.path
# 使用ADB命令
import re
import subprocess
import time

# 本地文件，设备文件
local_base_path = "base.zip"
local_file_path = "test.zip"
local_compair_path = "compair.zip"
remote_file_path = "sdcard/Download/test.zip"


def bytes_to_megabytes(bytes):
    return round(bytes / (1024 * 1024), 2)


# 查询所有在线设备
def get_adb_devices():
    try:
        # 执行adb devices命令
        result = subprocess.run(['adb', 'devices'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # 获取标准输出
        output = result.stdout
        # if "offline" in output:
        #     breakpoint()
        # 如果adb命令执行成功，则进一步处理输出
        if result.returncode == 0:
            # 移除标题行 ("List of devices attached")
            devices = output.split('\n')[1:-1]
            # 去除每行前面的空白字符并按需求格式化输出
            devices = [line.split('\t')[0] for line in devices if line.strip()]
            return devices
        else:
            # 如果adb命令执行失败，则打印错误信息
            print(result.stderr.strip())
    except Exception as e:
        print(f"An error occurred: {e}")
    return None


# 改进，还需要记录设备后的状态（offline,unauthorized,device状态）
def get_adb_map():
    time.sleep(40)
    # 初始化一个空字典来保存设备信息
    devices_map = {}
    # 执行adb devices命令
    result = subprocess.run(['adb', 'devices'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            check=True)
    # 获取标准输出
    output = result.stdout
    # if "offline" in output:
    #     subprocess.run(['adb', 'kill-server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    #     time.sleep(5)
    #     get_adb_map()
    # 如果adb命令执行成功，则进一步处理输出
    if result.returncode == 0:
        # 移除标题行 ("List of devices attached")
        devices = output.split('\n')[1:-1]
        # 去除每行前面的空白字符并按需求格式化输出
        devices = [line.split('\t') for line in devices if line.strip()]
        if not devices:
            devices_map["error"] = "设备为空"
        else:
            for device_info in devices:
                # 设备序列号和名称
                serial, name = device_info
                # 去除名称中的'\r'字符
                name = name.rstrip('\r')
                devices_map[serial] = name
    else:
        # 如果adb命令执行失败，则打印错误信息
        print(result.stderr.strip())
        devices_map["error"] = result.stderr.strip()
    # 打印设备字典
    print(devices_map)
    return devices_map


# 删除文件
def run_adb_rm(count, device):
    time.sleep(5)
    # 完整的adb命令
    adb_command = f"adb -s {device} shell rm -rf {remote_file_path}"
    try:
        # 执行adb命令
        result = subprocess.run(adb_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        print("4.删除文件结果：")
        print(result)
        # 记录对应端口的设备状态
        devices = get_adb_map()
        status = devices.get(device)
        logging.info(f"4删除平板中包数据,成功,{result}",
                     extra={'count': count, 'deviceID': device, 'result': status})
    except subprocess.CalledProcessError as e:
        print(f"adb命令执行错误：\n{e.stderr}")
        # 记录对应端口的设备状态
        devices = get_adb_map()
        status = devices.get(device)
        logging.error(f"4删除平板中包数据,失败, {e}",
                      extra={'count': count, 'deviceID': device, 'result': status})


# 使用ADB命令
def run_adb_push(count, device):
    time.sleep(5)
    # 完整的adb命令
    adb_command = f"adb -s {device} push {local_base_path} {remote_file_path}"
    try:
        # 执行adb命令
        result = subprocess.run(adb_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        # 获取标准输出
        output = result.stdout
        if "offline" in output:
            return "offline"
        print("5.推送文件结果：")
        print(result.stdout)
        pattern_cost_time = r'(\d+\.\d+)s'
        pattern_file_size = r'\d+(?= bytes in)'
        pattern_speed = r'(\d+\.\d+) MB/s'

        match_cost_time = re.search(pattern_cost_time, result.stdout)
        match_file_size = re.search(pattern_file_size, result.stdout)
        match_speed = re.search(pattern_speed, result.stdout)
        cost_time = match_cost_time.group()
        file_size_byte = match_file_size.group()
        speed = match_speed.group()
        file_size = bytes_to_megabytes(int(file_size_byte))
        # 记录对应端口的设备状态
        devices = get_adb_map()
        status = devices.get(device)
        logging.info(f"5推数据包,成功,{file_size}M文件共花费{cost_time}传输速率{speed}",
                     extra={'count': count, 'deviceID': device, 'result': status})
        return "success"
    except subprocess.CalledProcessError as e:
        print(f"adb命令执行错误：\n{e.stderr}")
        # 记录失败后对应端口的设备状态
        devices = get_adb_map()
        status = devices.get(device)
        logging.error(f"5推数据包,失败, {e.stdout}",
                      extra={'count': count, 'deviceID': device, 'result': status})
        return "offline"


# 使用ADB命令
def run_adb_pull(count, device, status):
    time.sleep(5)
    if os.path.isfile(local_compair_path):
        os.remove(local_compair_path)
        print(f"文件 {local_compair_path} 已被删除。")
    else:
        print(f"文件 {local_compair_path} 不存在。")
    # 完整的adb命令
    adb_command = f"adb -s {device} pull {remote_file_path} {local_compair_path} "
    try:
        # 执行adb命令
        result = subprocess.run(adb_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        print("12.拉取文件结果：")
        print(result.stdout)
        pattern_cost_time = r'(\d+\.\d+)s'
        pattern_file_size = r'\d+(?= bytes in)'
        pattern_speed = r'(\d+\.\d+) MB/s'

        match_cost_time = re.search(pattern_cost_time, result.stdout)
        match_file_size = re.search(pattern_file_size, result.stdout)
        match_speed = re.search(pattern_speed, result.stdout)
        cost_time = match_cost_time.group()
        file_size_byte = match_file_size.group()
        speed = match_speed.group()
        file_size = bytes_to_megabytes(int(file_size_byte))
        logging.info(f"12拉数据包,成功,{file_size}M文件共花费{cost_time}传输速率{speed}",
                     extra={'count': count, 'deviceID': device, 'result': status})
    except subprocess.CalledProcessError as e:
        print(f"adb命令执行错误：\n{e.stderr}")
        logging.error(f"12拉数据包,失败, {e}",
                      extra={'count': count, 'deviceID': device, 'result': status})


def calculate_sha256(file_path):
    """计算文件的SHA256哈希值并返回"""
    sha256_hash = hashlib.sha256()
    # 打开文件以读取字节
    with open(file_path, "rb") as f:
        # 读取并更新哈希值
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    # 返回SHA256哈希值的十六进制表示
    return sha256_hash.hexdigest()


def compare_files(count, device, status):
    """校验两个文件的完整性"""
    if not local_compair_path:
        print("13.文件推拉失败。")
        logging.info(f"13文件完整性校验,失败,文件推拉失败 \n",
                     extra={'count': count, 'deviceID': device, 'result': status})
    else:
        # 计算并比较两个文件的SHA256哈希值
        sha1_file1 = calculate_sha256(local_base_path)
        sha1_file2 = calculate_sha256(local_compair_path)

        if sha1_file1 == sha1_file2:
            print("13.两个文件完整性和一致性校验通过。")
            time.sleep(5)
            logging.info(f"13文件完整性校验,成功,SHA256哈希值:{sha1_file1} \n",
                         extra={'count': count, 'deviceID': device, 'result': status})
        else:
            print("13.两个文件完整性和一致性校验失败。")
            time.sleep(5)
            logging.error(f"13文件完整性校验,失败,SHA256哈希值:{sha1_file1}!={sha1_file2} \n",
                          extra={'count': count, 'deviceID': device, 'result': status})


def compare_devices_differences(map1, map2, log_file, count, step, device_id, devicePort_map):
    # 打开日志文件
    with open(log_file, 'a') as log:
        # 获取两个字典的并集，以找出不同的键
        combined_keys = set(map1.keys()).union(map2.keys())
        log.write(f"\n在第 '{count}' 轮次的'{step}'-步骤，执行端口号 '{devicePort_map.get(device_id)}'的设备 '{device_id}' 操作时的状态变化：\n")
        for key in combined_keys:
            # 如果 key 在 map1 (初始化查询设备列表)中有值而在 map2 (端口变化后设备列表)中没有，记录差异
            if key in map1 and key not in map2:
                log.write(f"端口号 '{devicePort_map.get(key)}'的设备 '{key}' 掉线了。\n")
            # 如果 key 在 map2 (端口变化后设备列表) 中有值而在 map1 (初始化查询设备列表) 中没有，记录差异
            elif key in map2 and key not in map1:
                log.write(f"端口号 '{devicePort_map.get(key)}'的设备 '{key}' 为新增连接。\n")
            # 如果 key 在两个 map 中都存在但值不同，记录差异
            elif key in map1 and key in map2 and map1[key] != map2[key]:
                log.write(f"端口号 '{devicePort_map.get(key)}'的设备 '{key}' 状态变化：{map1[key]}-->{map2[key]}\n")

    print(f"设备状态变化已写入日志文件 '{log_file}'。")


# 将一个字典（map）的值转换为另一个字典的键，并将所有值赋值为特定的字符串'device'
def transform_and_set_value(input_map):
    # 创建一个新的字典，其键为原字典的值，值为'device'
    new_map = {v: 'device' for v in input_map.values()}
    return new_map


def connection_lost(log_file, count, device_id, devicePort_map, lostCount):
    # 打开日志文件
    with open(log_file, 'a') as log:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log.write(f"\n{now}---端口号 '{devicePort_map.get(device_id)}'的设备 '{device_id}'在第 '{count}' 轮次掉线， 截至目前掉线'{lostCount}'次\n")
    print(f"离线设备已写入日志文件 '{log_file}'。")


def update_lostMap(map, key):
    """更新计数字典，如果键不存在则设置为1，如果存在则加1。

    参数:
    map : dict
        存储键和计数的字典。
    key : object
        要更新的键。
    """
    if key in map:
        map[key] += 1  # 如果键存在，增加它的计数
    else:
        map[key] = 1  # 如果键不存在，将它添加到字典并设置为1