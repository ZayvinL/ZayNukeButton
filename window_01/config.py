# c:/Users/liucx/.nuke/MyButton/window_01/config.py
# -*- coding: UTF-8 -*-
"""配置和辅助函数"""

import os
import json

import paths_setup as psp


def _get_user_db_path():
    """获取当前用户的数据库路径"""
    db_path = psp.user_db_path_get()
    config_path = psp.get_user_dbjson_path()
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"用户配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        db_uuid = config.get('current_db_uuid')
        
        if not db_uuid:
            raise ValueError("配置文件中未找到 current_db_uuid")
    
    db_path = os.path.join(db_path, f"tools_{db_uuid}.db")
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")
    
    return db_path


def _get_toolbox_path():
    """获取工具箱根目录路径"""
    return psp.tools_path_get()
