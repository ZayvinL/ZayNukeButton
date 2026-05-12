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
