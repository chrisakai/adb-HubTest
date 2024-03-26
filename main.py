# -*- coding: utf-8 -*-
import csv
import json
import logging
import time
import requests
from utils import get_adb_devices, read_yml, compare_files, run_adb_pull, run_adb_rm, run_adb_push, get_adb_map, \
    read_setting

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s , %(levelname)s , 第%(count)s轮次, %(deviceID)s, %(result)s, %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='log.csv',
                    filemode='w')


# 请求接口
openDoorURL = "http://127.0.0.1:8200/hub/openDoorOnly"
openAllURL = "http://127.0.0.1:8200/hub/openAll"
closeDoorURL = "http://127.0.0.1:8200/hub/closeDoorOnly"

count = 0

# 主程序
if __name__ == "__main__":
    # 读取配置文件列表
    hub_map = read_yml()
    setting = read_setting()
    round = setting.get("round")

    with open('log.csv', 'w', newline='') as csvfile:
        # 创建CSV写入器
        logwriter = csv.writer(csvfile)

    while True:
        if count == round:
            break
        count += 1

        # 0.开所有HUB，调用接口openAll(初始化保证查询到所有连接设备)
        try:
            response = requests.post(openAllURL)
            # 检查请求是否成功
            if response.status_code == 200:
                data = response.json()
                print(data)
                time.sleep(5)
                logging.info(f"开所有HUB,成功,{data}",
                             extra={'count': count, 'deviceID': "初始化", 'result': "初始化"})
            else:
                print(f"请求失败，状态码：{response.status_code}")
                logging.info(f"开所有HUB,失败,{response.status_code}",
                             extra={'count': count, 'deviceID': "初始化", 'result': "初始化"})
        except Exception as e:
            logging.error(f"开所有HUB,失败,{e}",
                          extra={'count': count, 'deviceID': "初始化", 'result': "初始化"})

        # 1.查所有设备在线状态 Adb devices(记录初始化后所有设备的状态信息)
        devices = get_adb_map()
        if not devices:
            logging.error(f"1查所有设备在线状态,失败,", extra={'count': count-1, 'deviceID': "新轮次", 'result': "出错：在线设备为空"})
            time.sleep(5)
            continue
        else:
            logging.info(f"1查所有设备在线状态,成功, {devices}", extra={'count': count, 'deviceID': "新轮次", 'result': "新轮次"})

            # 2.选择平板X
            # 循环列表中的所有设备执行压力测试
            for key in hub_map.keys():
                # 若列表中有设备在线
                if hub_map.get(key) in devices.keys():
                    print(key)
                    device_id = hub_map.get(key)
                    status = devices.get(device_id)
                    if status != "device":
                        logging.error(f"2选择平板,失败,状态为{status}",
                                     extra={'count': count, 'deviceID': device_id, 'result': status})
                        continue
                    logging.info(f"2选择平板,成功,状态为{status}",
                                 extra={'count': count, 'deviceID': device_id, 'result': status})
                    # 录入数组
                    json_array = json.dumps([key])
                    try:
                        # 3.关闭所有HUB开对应HUB，调用接口openDoorOnly（目的在于提升传输速率）
                        response3 = requests.post(openDoorURL, headers={'Content-Type': 'application/json'}, data=json_array)
                        # 检查请求是否成功
                        if response3.status_code == 200:
                            data = response3.json()
                            print(data)
                            time.sleep(5)
                            # 记录开启HUB后对应端口的设备状态
                            devices = get_adb_map()
                            status = devices.get(device_id)
                            logging.info(f"3开启HUB对应端口{key},成功,{data}",
                                         extra={'count': count, 'deviceID': device_id, 'result': status})
                        else:
                            print(f"请求失败，状态码：{response3.status_code}")
                            # 记录开启HUB后对应端口的设备状态
                            devices = get_adb_map()
                            status = devices.get(device_id)
                            logging.info(f"3开启HUB对应端口{key},失败,{response3.status_code}",
                                         extra={'count': count, 'deviceID': device_id, 'result': status})
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
                    run_adb_push(count, device_id)
                    # 6.开所有HUB，调用接口openAll（记录IO后在线设备是否受影响）
                    try:
                        response6 = requests.post(openAllURL)
                        # 检查请求是否成功
                        if response6.status_code == 200:
                            data = response6.json()
                            print(data)
                            time.sleep(5)
                            # todo 若设备上下线情况变化
                            logging.info(f"6开所有HUB,成功,{data}",
                                         extra={'count': count, 'deviceID': device_id, 'result': status})
                        else:
                            print(f"请求失败，状态码：{response6.status_code}")
                            logging.info(f"6开所有HUB,失败,{response6.status_code}",
                                         extra={'count': count, 'deviceID': device_id, 'result': status})
                            continue
                    except Exception as e:
                        logging.error(f"6开所有HUB,失败,{e}",
                                      extra={'count': count, 'deviceID': device_id, 'result': status})
                        continue
                    try:
                        # 7.查所有设备在线状态 Adb devices（记录IO后在线设备是否受影响）
                        devices = get_adb_map()
                        status = devices.get(device_id)
                        if not devices:
                            logging.error(f"7查所有设备在线状态,失败,",
                                          extra={'count': count, 'deviceID': device_id, 'result': "出错：在线设备为空"})
                            continue
                        elif status != "device":
                            logging.error(f"7在线状态,失败, {device_id}该设备状态为{status}",
                                          extra={'count': count, 'deviceID': device_id, 'result': status})
                            continue
                        else:
                            logging.info(f"7查所有设备在线状态,成功,{devices}",
                                         extra={'count': count, 'deviceID': device_id, 'result': status})
                    except Exception as e:
                        logging.error(f"7查所有设备在线状态,失败,{e}",
                                      extra={'count': count, 'deviceID': device_id, 'result': "adb执行异常"})
                        continue
                    try:
                        # 8.关对应HUB，调用接口closeDoorOnly（模拟领取任务后的拔出操作）
                        response8 = requests.post(closeDoorURL, data=json_array, headers={'Content-Type': 'application/json'})
                        # 检查请求是否成功
                        if response8.status_code == 200:
                            data = response8.json()
                            print(data)
                            logging.info(f"8关闭HUB对应端口{key},成功,{data}",
                                         extra={'count': count, 'deviceID': device_id, 'result': status})
                        else:
                            print(f"请求失败，状态码：{response8.status_code}")
                            logging.info(f"8关闭HUB对应端口{key},失败,{response8.status_code}",
                                         extra={'count': count, 'deviceID': device_id, 'result': status})
                            continue
                    except Exception as e:
                        logging.error(f"8关闭HUB对应端口{key},失败,{e}",
                                      extra={'count': count, 'deviceID': device_id, 'result': status})
                        continue
                    try:
                        # 9.开对应HUB，调用接口openDoorOnly（模拟领取任务后执行完归还的插入操作）
                        response9 = requests.post(openDoorURL, data=json_array, headers={'Content-Type': 'application/json'})
                        # 检查请求是否成功
                        if response9.status_code == 200:
                            data = response9.json()
                            print(data)
                            logging.info(f"9开启HUB对应端口{key},成功,{data}",
                                         extra={'count': count, 'deviceID': device_id,  'result': status})
                            time.sleep(5)
                        else:
                            print(f"请求失败，状态码：{response9.status_code}")
                            logging.info(f"9开启HUB对应端口{key},失败,{response9.status_code}",
                                         extra={'count': count, 'deviceID': device_id, 'result': status})
                            continue
                    except Exception as e:
                        logging.error(f"9开启HUB对应端口{key},失败,{e}",
                                      extra={'count': count, 'deviceID': device_id, 'result': status})
                        continue
                    try:
                        # 10.查所有设备在线状态 Adb devices（检查插拔对应设备对其余设备状态有无影响）
                        devices = get_adb_map()
                        status = devices.get(device_id)
                        if not devices:
                            logging.error(f"10查所有设备在线状态,失败,出错：在线设备为空",
                                          extra={'count': count, 'deviceID': device_id, 'result': status})
                            time.sleep(5)
                            continue
                        elif status != "device":
                            logging.error(f"10查所有设备在线状态,失败,出错：{device_id}该设备状态为{status}",
                                          extra={'count': count, 'deviceID': device_id, 'result': status})
                            continue
                        else:
                            logging.info(f"10查所有设备在线状态,成功,{devices}",
                                         extra={'count': count, 'deviceID': device_id, 'result': status})
                    except Exception as e:
                        logging.error(f"10查所有设备在线状态,失败,{e}",
                                      extra={'count': count, 'deviceID': device_id, 'result': status})
                        time.sleep(5)
                        continue
                    try:
                        # 11.关闭所有HUB开对应HUB，调用接口openDoorOnly（提升传输速率）
                        response11 = requests.post(openDoorURL, data=json_array, headers={'Content-Type': 'application/json'})
                        # 检查请求是否成功
                        if response11.status_code == 200:
                            data = response11.json()
                            print(data)
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
                    # todo 增加是否拉取成功判断
                    run_adb_pull(count, device_id, status)
                    # 14.利用sha256校验文件完整性
                    try:
                        compare_files(count, device_id, status)
                    except Exception as e:
                        time.sleep(5)
                        logging.error(f"14文件完整性校验,失败,{e} \n",
                                      extra={'count': count, 'deviceID': device_id, 'result': status})
                        continue
                else:
                    print("设备不在线")
                    logging.info(f"2选择平板,失败,设备{hub_map.get(key)}未连接 \n",
                                 extra={'count': count, 'deviceID': hub_map.get(key), 'result': "未连接"})
                    time.sleep(5)


