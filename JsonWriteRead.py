# -*- coding: UTF-8 -*-
import json


# ----------------------------------------------------------------------------------------------------------------------------------#

# Liu xiao bo
# Linden Bo
# liucxiaobo@outlook.com

# 写入json文件
# 读取json文件
# ----------------------------------------------------------------------------------------------------------------------------------#



# 写入json文件
def WriteJson(path=None, dict_data={}):
    # Json write
    try:
        Writedata = json.dumps(dict_data, ensure_ascii=False, sort_keys=True, indent=4)
        with open(path, "w", encoding='utf-8') as f:
            f.write(Writedata)
    except:
        print("写入错误")


# 读取json文件
def ReadJson(path=None):
    # Json Read
    try:
        with open(path, 'r', encoding='utf-8') as load_f:
            load_dict = json.load(load_f)
        return load_dict   
    except PermissionError:
        print(f"没有权限读取文件：{path}")
        return {}  # 权限错误时返回空字典
    except FileNotFoundError:
        print(f"文件不存在：{path}")
        return {}  # 可选：文件不存在时也返回空字典
    except Exception as e:
        print(f"读取失败：{str(e)}")
        return {}  # 其他错误也返回空字典