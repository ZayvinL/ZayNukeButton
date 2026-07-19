# Copyright 2026 LIUXIAOBO (刘晓波)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
