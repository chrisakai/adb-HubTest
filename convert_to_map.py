def convert_to_map(file_path):
    my_map = {}
    # 打开文件读取内容
    with open(file_path, 'r') as file:
        for line in file:
            # 去除每行的空白字符（包括换行符）
            line = line.strip()
            # 检查行是否非空
            if line:
                # 拆分行以创建键值对
                key, value = line.split(':')
                key = int(key)  # 将字符串形式的键转换为整数
                value = value.strip()  # 去除值前后可能的空白字符
                my_map[key] = value  # 将键值对添加到字典中
    return my_map