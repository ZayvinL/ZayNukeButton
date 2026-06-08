# MyButton — 安装说明

Nuke 工具搜索与管理系统，支持多用户共享、工具导出、搜索过滤、元数据编辑等。

---

## 一、环境要求

| 依赖 | 说明 |
|---|---|
| **Nuke** | 12.0 及以上（需支持 PySide2/PySide6） |
| **Python** | Nuke 内置 Python 即可 |
| **系统** | Windows / Linux / macOS |

---

## 二、安装步骤

### 2.1 下载项目

将项目克隆或下载到 Nuke 的 `.nuke` 目录下：

```bash
# 进入 Nuke 配置目录
cd ~/.nuke

# 克隆项目
git clone https://github.com/你的用户名/MyButton.git
```

最终目录结构如下：

```
~/.nuke/MyButton/
├── menu.py
├── window_panel.py
├── settool.py
├── paths_setup.py
├── sqlite_file_setup.py
├── ...
├── tools/
├── styles/
├── pnghelp/
└── window_01/
```

### 2.2 加载到 Nuke

在 Nuke 的 `~/.nuke/init.py`（或 `~/.nuke/menu.py`）中添加：

```python
# MyButton 工具搜索系统
import nuke
nuke.pluginAddPath('./MyButton')
import menu
```

启动 Nuke 后，Nodes 菜单栏会新增 **Z** 菜单，包含 MyButton、Export、Install 等入口。

---

## 三、数据目录分离（多用户部署推荐）

### 3.1 为什么要修改

默认情况下，数据库、用户配置、工具文件等所有数据都存放在工具安装目录（`~/.nuke/MyButton/`）下。在多用户共享环境（如工作室服务器）中，建议将数据指向一个独立的共享目录，方便：

- 统一设置数据目录权限，所有用户都能读写
- 工具代码和数据分开管理，更新代码不影响数据
- 不同机器、不同用户访问同一份数据

### 3.2 修改方法

编辑 `paths_setup.py`，找到 `local_path_get()` 函数，将返回值改为你想要的数据存储路径：

```python
def local_path_get():
    # 原来：返回工具所在目录
    # currentPath = os.path.dirname(os.path.abspath(__file__)) + "/"

    # 改为：返回统一的数据存储路径
    # Windows 示例：
    currentPath = "G:/MyButton_Data/"
    # Linux/Mac 示例：
    # currentPath = "/mnt/share/MyButton_Data/"
    return currentPath
```

### 3.3 设置数据目录权限

修改路径后，对数据目录设置共享权限，确保所有用户可读写。以管理员身份在 Nuke Script Editor 中运行一次：

```python
import paths_setup, QuanXianSet

QuanXianSet.setup_directory_shared_permissions(paths_setup.local_path_get())
```

- **Windows**：需以管理员身份运行 Nuke
- **Linux/Mac**：需 sudo 权限

### 3.4 配置后的结构

```
# 工具代码（只读即可，各用户 .nuke 下）
~/.nuke/MyButton/
├── menu.py
├── window_panel.py
├── paths_setup.py        ← local_path_get() 已指向数据目录
├── ...

# 所有数据（共享目录，所有用户读写）
G:/MyButton_Data/
├── tools/                 ← 工具文件
├── styles/                ← 样式文件
├── pnghelp/               ← 帮助图片
├── SQLite_file/           ← 数据库文件
├── users/                 ← 用户配置
└── tempexport/            ← 临时导出
```

---

## 四、切换快捷键

主面板的快捷键在 `menu.py` 第 25 行附近：

```python
toolbar.addCommand('Button/MyButton', window_panel.run_show, "Alt+W", shortcutContext=2)
```

将第三个参数改为你想要的快捷键即可。修改后点击菜单 **Z → Refresh hotkey** 刷新生效。

搜索窗口内的关闭快捷键在 `window_01/search_window.py`：

```python
esc_shortcut2 = QShortcut(QKeySequence("Alt+W"), self)
```

---

## 五、验证安装

1. 启动 Nuke
2. 在 Nodes 菜单栏确认 **Z** 菜单出现
3. 按快捷键或点击 **Z → MyButton**，确认搜索面板弹出
4. 选中任意节点后再次打开面板，确认自动填入过滤条件
5. 点击 **Z → Install** 打开工具管理界面，确认数据库初始化成功
