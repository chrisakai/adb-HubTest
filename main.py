# -*- coding: utf-8 -*-
import csv
import datetime
import json
import logging

import subprocess
import time

import requests
# import autoMappingPort

from staticTools import read_yml, read_setting, getDevicePortMap
from utils import compare_files, run_adb_pull, run_adb_rm, run_adb_push, get_adb_map, compare_devices_differences, \
    transform_and_set_value

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s , %(levelname)s , 第%(count)s轮次, %(deviceID)s, %(result)s, %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='log.csv',
                    filemode='w')

# 测试日日期
date = datetime.date.today()
# 读取配置文件列表
hub_map = read_yml()
setting = read_setting()
round = setting.get("round")
devices_map_log = 'devices_map_change' + str(date) + '.log'
devicePort_map = getDevicePortMap()
# 请求接口
openDoorURL = "http://127.0.0.1:8200/hub/openDoor"
openAllURL = "http://127.0.0.1:8200/hub/openAll"
closeAllURL = "http://127.0.0.1:8200/hub/closeAll"
devicesInfoURL = "http://127.0.0.1:8200/link/devicesInfo"

count = 0

# 主程序
if __name__ == "__main__":

    # exec('autoMappingPort')

    with open('log.csv', 'w', newline='') as csvfile:
        # 创建CSV写入器
        logwriter = csv.writer(csvfile)

    while True:
        if count == round:
            break
        count += 1

        # 循环列表中的所有设备执行压力测试
        for key in hub_map.keys():

            # 0.开所有HUB，调用接口openAll(初始化保证查询到所有连接设备)
            try:
                response = requests.post(openAllURL)
                # 检查请求是否成功
                if response.status_code == 200:
                    data = response.json()
                    print("0开所有HUB" + str(data))
                    time.sleep(5)
                    logging.info(f"开所有HUB,成功,{data}",
                                 extra={'count': count, 'deviceID': "初始化", 'result': "初始化"})
                else:
                    print(f"请求失败，状态码：{response.status_code}")
                    logging.error(f"开所有HUB,失败,{response.status_code}",
                                  extra={'count': count, 'deviceID': "初始化", 'result': "初始化"})
            except Exception as e:
                logging.error(f"开所有HUB,失败,{e}",
                              extra={'count': count, 'deviceID': "初始化", 'result': "初始化"})

            # 1.查所有设备在线状态 Adb devices(记录初始化后所有设备的状态信息)
            devices_init = get_adb_map()
            if not devices_init:
                logging.error(f"1查所有设备在线状态,失败,",
                              extra={'count': count - 1, 'deviceID': "尚未选择设备", 'result': "出错：在线设备为空"})
                time.sleep(5)
                continue
            else:
                print("1.查所有设备在线状态")
                logging.info(f"1查所有设备在线状态,成功, {devices_init}",
                             extra={'count': count, 'deviceID': "尚未选择设备", 'result': "详细见查询结果列"})
                print("1.1查所有终端信息并记入日志")
                try:
                    responseDevicesInfo = requests.get(devicesInfoURL)
                    # 检查请求是否成功
                    if responseDevicesInfo.status_code == 200:
                        data = responseDevicesInfo.json()
                        logging.info(f"1.1查所有设备信息,成功, {data}",
                                     extra={'count': count, 'deviceID': "info", 'result': "info"})
                    else:
                        logging.info(f"1.1查所有设备信息,失败")
                except Exception as e:
                    logging.error(f"1.1查所有设备信息,失败,{e}")
                compare_devices_differences(transform_and_set_value(hub_map), devices_init, devices_map_log, count,
                                            "1查所有设备在线状态", "尚未选择设备", devicePort_map)
            # 若列表中有设备在线
            if hub_map.get(key) in devices_init.keys():
                print("2.选择端口:" + str(key))
                # 2.选择平板X
                device_id = hub_map.get(key)
                status = devices_init.get(device_id)
                if status != "device":
                    logging.error(f"2选择平板,失败,状态为{status}",
                                  extra={'count': count, 'deviceID': device_id, 'result': status})
                    continue
                logging.info(f"2选择平板,成功,状态为{status}",
                             extra={'count': count, 'deviceID': device_id, 'result': status})
                try:
                    # 2.5关所有HUB，closeAllURL（模拟领取任务后的拔出操作）
                    responseCloseAll = requests.post(closeAllURL)
                    # 检查请求是否成功
                    if responseCloseAll.status_code == 200:
                        data = responseCloseAll.json()
                        print("2.5关闭所有HUB:" + str(data))
                        logging.info(f"2.5关闭所有HUB,成功,{data}",
                                     extra={'count': count, 'deviceID': device_id, 'result': status})
                    else:
                        print(f"请求失败，状态码：{responseCloseAll.status_code}")
                        logging.error(f"2.5关闭所有HUB,失败,{responseCloseAll.status_code}",
                                      extra={'count': count, 'deviceID': device_id, 'result': status})
                        continue
                except Exception as e:
                    logging.error(f"2.5关闭所有HUB,失败,{e}",
                                  extra={'count': count, 'deviceID': device_id, 'result': status})
                    continue
                # 录入数组
                json_array = json.dumps([key])
                retry = 0
                try:
                    while retry < 3:
                        responseCloseAll = requests.post(closeAllURL)
                        if responseCloseAll.status_code != 200:
                            continue
                        time.sleep(30)
                        # 3.关闭所有HUB开对应HUB，调用接口openDoorOnly（目的在于提升传输速率）
                        response3 = requests.post(openDoorURL, headers={'Content-Type': 'application/json'},
                                                  data=json_array)
                        # 检查请求是否成功
                        if response3.status_code == 200:
                            data = response3.json()
                            print("3.开对应HUB" + str(data))
                            time.sleep(5)
                            # 记录开启HUB后对应端口的设备状态
                            devices = get_adb_map()
                            status = devices.get(device_id)
                            logging.info(f"3.5查所有设备,成功,{devices}",
                                         extra={'count': count, 'deviceID': device_id, 'result': status})
                            if status == "offline":
                                retry += 1
                                logging.info(f"3开启HUB对应端口{key}:状态为offline,重试第{retry}次,{data}",
                                             extra={'count': count, 'deviceID': device_id, 'result': "retry"})
                                continue
                            else:
                                logging.info(f"3开启HUB对应端口{key},成功,{data}",
                                             extra={'count': count, 'deviceID': device_id, 'result': status})
                                break
                        else:
                            print(f"请求失败，状态码：{response3.status_code}")
                            # 记录开启HUB后对应端口的设备状态
                            devices = get_adb_map()
                            if devices.get("error"):
                                status = devices.get("error")
                            else:
                                status = devices.get(device_id)
                            logging.error(f"3开启HUB对应端口{key},失败,{response3.status_code}",
                                          extra={'count': count, 'deviceID': device_id, 'result': status})
                            continue
                    if retry == 3:
                        logging.info(f"3开启HUB对应端口{key}:状态为offline,重试第{retry}次已达上限,{data} \n",
                                     extra={'count': count, 'deviceID': device_id, 'result': status})
                        logging.info(
                            f"开始尝试重启adb server,重启adb server",
                            extra={'count': count, 'deviceID': device_id, 'result': status})
                        subprocess.run(['adb', 'kill-server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True)
                        time.sleep(30)
                        continue
                except Exception as e:
                    # 记录开启HUB后对应端口的设备状态
                    devices = get_adb_map()
                    status = devices.get(device_id)
                    logging.error(f"3开启HUB对应端口{key},失败,{e}",
                                  extra={'count': count, 'deviceID': device_id, 'result': status})
                    continue
                # 4.删除平板中包，adb shell rm /path/to/example.txt
                run_adb_rm(count, device_id)
                # 5.推数据包，adb push path/to/local/file /path/on/device
                pushretry = 0
                try:
                    while pushretry < 3:
                        if run_adb_push(count, device_id) == "offline":
                            responseCloseAll = requests.post(closeAllURL)
                            if responseCloseAll.status_code != 200:
                                continue
                            time.sleep(30)
                            # 3.关闭所有HUB开对应HUB，调用接口openDoorOnly（目的在于提升传输速率）
                            responseRetry = requests.post(openDoorURL, headers={'Content-Type': 'application/json'},
                                                          data=json_array)
                            # 检查请求是否成功
                            if responseRetry.status_code == 200:
                                data = responseRetry.json()
                                print("offline重试开对应HUB" + str(data))
                                time.sleep(5)
                                # 记录开启HUB后对应端口的设备状态
                                devices = get_adb_map()
                                status = devices.get(device_id)
                                logging.info(f"offline重试查所有设备,成功,{devices}",
                                             extra={'count': count, 'deviceID': device_id, 'result': "retry"})
                                if status == "offline":
                                    pushretry += 1
                                    logging.info(
                                        f"offline重试开启HUB对应端口{key}失败:状态为offline,重试第{pushretry}次,{data}",
                                        extra={'count': count, 'deviceID': device_id, 'result': "retry"})
                                    continue
                                else:
                                    pushretry += 1
                                    logging.info(f"offline重试开启HUB对应端口{key},成功,重试第{pushretry}次,{data}",
                                                 extra={'count': count, 'deviceID': device_id, 'result': "retry"})
                                    continue
                            else:
                                print(f"请求失败，状态码：{responseRetry.status_code}")
                                # 记录开启HUB后对应端口的设备状态
                                devices = get_adb_map()
                                if devices.get("error"):
                                    status = devices.get("error")
                                else:
                                    status = devices.get(device_id)
                                pushretry += 1
                                logging.error(
                                    f"offline重试开启HUB对应端口{key},失败,重试第{pushretry}次,{responseRetry.status_code}",
                                    extra={'count': count, 'deviceID': device_id, 'result': status})
                                continue
                        else:
                            break
                    if pushretry == 3:
                        logging.info(f"offline重试开启HUB对应端口{key}失败:状态为offline,重试第{pushretry}次已达上限 \n",
                                     extra={'count': count, 'deviceID': device_id, 'result': "retry"})
                        logging.info(
                            f"开始尝试重启adb server,重启adb server",
                            extra={'count': count, 'deviceID': device_id, 'result': status})
                        subprocess.run(['adb', 'kill-server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True)
                        time.sleep(30)
                        continue
                except Exception as e:
                    # 记录开启HUB后对应端口的设备状态
                    devices = get_adb_map()
                    status = devices.get(device_id)
                    logging.error(f"5推数据包,失败,{e}",
                                  extra={'count': count, 'deviceID': device_id, 'result': status})
                    continue

                # 6.开所有HUB，调用接口openAll（记录IO后在线设备是否受影响）
                try:
                    response6 = requests.post(openAllURL)
                    # 记录对应端口的设备状态
                    devices = get_adb_map()
                    status = devices.get(device_id)
                    # 检查请求是否成功
                    if response6.status_code == 200:
                        data = response6.json()
                        print("6.开所有HUB" + str(data))
                        time.sleep(5)
                        logging.info(f"6开所有HUB,成功,{data}",
                                     extra={'count': count, 'deviceID': device_id, 'result': status})
                    else:
                        print(f"请求失败，状态码：{response6.status_code}")
                        logging.error(f"6开所有HUB,调用柜控接口失败,{response6.status_code}",
                                      extra={'count': count, 'deviceID': device_id, 'result': status})
                        continue
                except Exception as e:
                    logging.error(f"6开所有HUB,失败,{e}",
                                  extra={'count': count, 'deviceID': device_id, 'result': status})
                    # 若设备上下线情况变化，记录到单独的日志文件中
                    devices_after = get_adb_map()
                    compare_devices_differences(devices_init, devices_after, devices_map_log, count, "6开所有HUB",
                                                device_id, devicePort_map)
                    continue
                try:
                    # 7.查所有设备在线状态 Adb devices（记录IO后在线设备是否受影响）
                    devices7 = get_adb_map()
                    status = devices7.get(device_id)
                    print("7.查所有设备在线状态中")
                    if not devices7:
                        logging.error(f"7查所有设备在线状态,失败, \n",
                                      extra={'count': count, 'deviceID': device_id, 'result': "出错：在线设备为空"})
                        compare_devices_differences(devices_init, devices7, devices_map_log, count,
                                                    "7查所有设备在线状态", device_id, devicePort_map)
                        continue
                    elif status != "device":
                        logging.error(f"7在线状态,失败, {device_id}该设备状态为{status} \n",
                                      extra={'count': count, 'deviceID': device_id, 'result': status})
                        compare_devices_differences(devices_init, devices7, devices_map_log, count,
                                                    "7查所有设备在线状态", device_id, devicePort_map)
                        continue
                    else:
                        logging.info(f"7查所有设备在线状态,成功,{devices7}",
                                     extra={'count': count, 'deviceID': device_id, 'result': status})
                        compare_devices_differences(devices_init, devices7, devices_map_log, count,
                                                    "7查所有设备在线状态", device_id, devicePort_map)
                except Exception as e:
                    logging.error(f"7查所有设备在线状态,失败,{e} \n",
                                  extra={'count': count, 'deviceID': device_id, 'result': "adb执行异常"})
                    compare_devices_differences(devices_init, devices7, devices_map_log, count,
                                                "7查所有设备在线状态", device_id, devicePort_map)
                    continue
                try:
                    # 8.关所有HUB，closeAllURL（模拟领取任务后的拔出操作）
                    print("8.关所有HUB")
                    response8 = requests.post(closeAllURL)
                    devices_after = get_adb_map()
                    status = devices_after.get(device_id)
                    # 检查请求是否成功
                    if response8.status_code == 200:
                        data = response8.json()
                        print("8.关闭所有HUB:" + str(data))
                        logging.info(f"8关闭所有HUB,成功,{data}",
                                     extra={'count': count, 'deviceID': device_id, 'result': status})
                    else:
                        print(f"请求失败，状态码：{response8.status_code}")
                        logging.error(f"8关闭所有HUB,失败,{response8.status_code}",
                                      extra={'count': count, 'deviceID': device_id, 'result': status})
                        continue
                except Exception as e:
                    logging.error(f"8关闭所有HUB,失败,{e}",
                                  extra={'count': count, 'deviceID': device_id, 'result': status})
                    continue
                try:
                    time.sleep(5)
                    # 9.开对应HUB，调用接口openDoorOnly（模拟领取任务后执行完归还的插入操作）
                    response9 = requests.post(openDoorURL, data=json_array,
                                              headers={'Content-Type': 'application/json'})
                    # 检查请求是否成功
                    if response9.status_code == 200:
                        retry = 0
                        while retry < 3:
                            devices_after = get_adb_map()
                            status = devices_after.get(device_id)
                            if status == "offline" or status == "设备为空" or status == "None":
                                retry += 1
                                print("重新尝试第" + str(retry) + "次查询")
                                continue
                            # elif status == "None":
                            #     breakpoint()
                            else:
                                break
                        data = response9.json()
                        print("9.开启HUB对应端口:" + str(key) + "  " + str(data))
                        logging.info(f"9开启HUB对应端口{key},成功,{data}",
                                     extra={'count': count, 'deviceID': device_id, 'result': status})
                        time.sleep(5)
                    else:
                        print(f"请求失败，状态码：{response9.status_code}")
                        logging.error(f"9开启HUB对应端口{key},调用柜控接口失败,{response9.status_code}",
                                      extra={'count': count, 'deviceID': device_id, 'result': status})
                        continue
                except Exception as e:
                    logging.error(f"9开启HUB对应端口{key},失败,{e}",
                                  extra={'count': count, 'deviceID': device_id, 'result': status})
                    # 若设备上下线情况变化，记录到单独的日志文件中
                    devices_after = get_adb_map()
                    compare_devices_differences(devices_init, devices_after, devices_map_log, count, "9开启HUB对应端口",
                                                device_id, devicePort_map)
                    continue
                try:
                    # 10.查对应设备在线状态 Adb devices
                    devices = get_adb_map()
                    if devices.get("error"):
                        status = devices.get("error")
                    else:
                        status = devices.get(device_id)
                    if not devices:
                        logging.error(f"10查所有设备在线状态,失败,出错：在线设备为空",
                                      extra={'count': count, 'deviceID': device_id, 'result': status})
                        time.sleep(5)
                        continue
                    else:
                        print("10.查所有设备在线状态中")
                        logging.info(f"10查所有设备在线状态,成功,{devices}",
                                     extra={'count': count, 'deviceID': device_id, 'result': status})
                except Exception as e:
                    logging.error(f"10查所有设备在线状态,失败,{e}",
                                  extra={'count': count, 'deviceID': device_id, 'result': status})
                    time.sleep(5)
                    continue
                try:
                    # 11.关闭所有HUB开对应HUB，调用接口openDoorOnly（提升传输速率）
                    response11 = requests.post(openDoorURL, data=json_array,
                                               headers={'Content-Type': 'application/json'})
                    # 检查请求是否成功
                    if response11.status_code == 200:
                        data = response11.json()
                        print("11.开启HUB对应端口" + str(key) + "  " + str(data))
                        logging.info(f"11开启HUB对应端口{key},成功,{data}",
                                     extra={'count': count, 'deviceID': device_id, 'result': status})
                    else:
                        print(f"请求失败，状态码：{response11.status_code}")
                        logging.info(f"11开启HUB对应端口{key},失败,{response11.status_code}",
                                     extra={'count': count, 'deviceID': device_id, 'result': status})
                        continue
                except Exception as e:
                    logging.error(f"11开启HUB对应端口{key},失败,{e}",
                                  extra={'count': count, 'deviceID': device_id, 'result': status})
                    continue
                # 12.拉数据包，adb pull /path/on/device path/to/local/file
                run_adb_pull(count, device_id, status)
                # 13.利用sha256校验文件完整性
                try:
                    compare_files(count, device_id, status)
                except Exception as e:
                    time.sleep(5)
                    logging.error(f"13文件完整性校验,失败,{e} \n",
                                  extra={'count': count, 'deviceID': device_id, 'result': status})
                    continue
            else:
                print("2.设备不在线")
                logging.info(f"2选择平板,失败,设备{hub_map.get(key)}未连接 \n",
                             extra={'count': count, 'deviceID': hub_map.get(key), 'result': "未连接"})
                time.sleep(5)
