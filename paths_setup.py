import os

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
