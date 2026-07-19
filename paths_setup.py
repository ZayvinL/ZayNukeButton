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

import os
import getpass

# 当前工具所在的路径地址
def local_path_get():
    currentPath = os.path.dirname(os.path.abspath(__file__)) + "/"
    # currentPath = os.path.normcase(currentPath)
    currentPath = currentPath.replace(os.sep,"/")
    return currentPath

# tools
def tools_path_get():
    toolsPath = local_path_get() + "tools/"
    # 确保输出文件夹存在
    os.makedirs(toolsPath, exist_ok=True)
    return toolsPath

# styles
def styles_path_get():
    stylesPath = local_path_get() + "styles/"
    return stylesPath

# users
def users_path_get():
    usersPath = local_path_get() + "users/"
    return usersPath


# pngfiles
def pngfiles_path_get():
    pngfilesPath = local_path_get() + "pnghelp/"
    return pngfilesPath

# 用户数据库集合
def user_db_path_get():
    userDbPath = local_path_get() + "SQLite_file/" 
    return userDbPath

def get_current_user():
    """获取当前系统用户名"""
    return getpass.getuser()

# 获取user 的数据库 db
def get_user_dbjson_path():
    currentUser = get_current_user()
    userPath = local_path_get() + "users/" + currentUser + "/db_config.json" 
    return userPath

# 临时存放
def tempexportpath_get():
    tempexportpath = local_path_get() + "tempexport/"
    # 确保输出文件夹存在
    os.makedirs(tempexportpath, exist_ok=True)
    return tempexportpath
