from utils import read_yml


class StaticTools:
    devicePort_map = {}

    @staticmethod
    # 通过字典推导式来实现将一个字典中的值作为新字典的键，并将新字典的值全部赋值为旧字典的键
    def transform_map():
        hub_map = read_yml()
        # 创建一个新的字典，其键为原字典的值，值为原字典的键
        transformed_map = {value: key for key, value in hub_map.items()}
        devicePort_map = transformed_map
        return devicePort_map
