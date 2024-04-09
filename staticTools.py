import yaml


def read_yml():
    with open("devices.yaml", "r") as file:
        config_data = yaml.safe_load(file)
        # 转换为字典
    config_map = {}
    for key, value in config_data.items():
        if isinstance(value, dict):
            nested_map = read_yml()
            config_map[key] = nested_map
        elif isinstance(value, list):
            nested_list = []
            for item in value:
                if isinstance(item, dict):
                    nested_list.append(read_yml())
                else:
                    nested_list.append(item)
            config_map[key] = nested_list
        else:
            config_map[key] = value

    return config_map


def read_setting():
    with open("setting.yaml", "r") as file:
        config_data = yaml.safe_load(file)
        # 转换为字典
    config_map = {}
    for key, value in config_data.items():
        if isinstance(value, dict):
            nested_map = read_yml()
            config_map[key] = nested_map
        elif isinstance(value, list):
            nested_list = []
            for item in value:
                if isinstance(item, dict):
                    nested_list.append(read_yml())
                else:
                    nested_list.append(item)
            config_map[key] = nested_list
        else:
            config_map[key] = value

    return config_map


# 通过字典推导式来实现将一个字典中的值作为新字典的键，并将新字典的值全部赋值为旧字典的键
def getDevicePortMap():
    hub_map = read_yml()
    # 创建一个新的字典，其键为原字典的值，值为原字典的键
    transformed_map = {value: key for key, value in hub_map.items()}
    return transformed_map
