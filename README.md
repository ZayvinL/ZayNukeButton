# MyButton / ZayNukeButton

Nuke 工具搜索与管理系统 — 快捷键唤起，多条件搜索，一键执行。

A Nuke tool search & management system — hotkey to launch, multi-condition search, one-click execution.

---

## 功能 / Features

| | |
|---|---|
| **工具搜索面板** | 快捷键唤起，支持按类名、标签、路径、名称多条件组合搜索 |
| **Tool Search** | Hotkey-launched panel with multi-condition search by class, tag, path, name |
| **节点感知** | 自动识别当前选中节点类型，智能过滤匹配工具 |
| **Node-Aware** | Auto-detects selected node types and filters matching tools |
| **工具管理** | 安装/卸载/收藏、重命名、移动目录、图标管理、帮助文档 |
| **Tool Manager** | Install, uninstall, favorite, rename, move, icon & help doc management |
| **导出工具** | 一键将选中节点或代码导出为可复用工具 |
| **Export** | One-click export selected nodes or code as reusable tools |
| **多用户支持** | SQLite 数据库隔离，共享权限一键配置 |
| **Multi-User** | Isolated SQLite databases, one-click shared permission setup |

---

## 代码仓库 / Repositories

| 平台 | 地址 |
|------|------|
| **GitHub**（主仓库） | [https://github.com/ZayvinL/ZayNukeButton](https://github.com/ZayvinL/ZayNukeButton) |
| **Gitee**（镜像） | [https://gitee.com/q-wuan90/ZayNukeButton](https://gitee.com/q-wuan90/ZayNukeButton) |

> Gitee 镜像与 GitHub 主仓库保持同步，中国大陆用户可通过 Gitee 获得更快的访问速度。

---

## 快速安装 / Quick Start

```bash
cd ~/.nuke
# GitHub
git clone https://github.com/ZayvinL/ZayNukeButton.git
# Gitee（国内推荐）
git clone https://gitee.com/q-wuan90/ZayNukeButton.git
```

在 `~/.nuke/init.py` 中添加 / Add to `~/.nuke/init.py`:

```python
import nuke
nuke.pluginAddPath('./ZayNukeButton')
import menu
```

启动 Nuke，Nodes 菜单栏出现 **Z** 菜单即安装成功。

Launch Nuke — a **Z** menu appears in the Nodes toolbar when installed.

---

## 多用户部署 / Multi-User Deployment

编辑 `paths_setup.py`，将 `local_path_get()` 的返回值改为统一的数据目录，然后对该目录设置一次共享权限即可。详见 [INSTALL.md](./INSTALL.md)。

Edit `paths_setup.py`, change `local_path_get()` to point to a shared data directory, then set shared permissions once. See [INSTALL.md](./INSTALL.md).

---

## 目录结构 / Structure

```
ZayNukeButton/
├── menu.py                 # Nuke 菜单入口 / menu entry
├── window_panel.py         # 搜索窗口启动器 / search window launcher
├── settool.py              # 工具管理主应用 / tool manager main app
├── paths_setup.py          # 路径管理 / path config
├── sqlite_file_setup.py    # 数据库管理 / database config
├── qt_imports.py           # PySide6/PySide2 兼容层 / Qt compat layer
├── tools/
│   └── githubTools/        # 示例工具 / example tools
├── window_01/              # 搜索窗口模块 / search window module
└── INSTALL.md              # 安装说明 / install guide
```

---

## 依赖 / Dependencies

- Nuke 12.0+
- PySide2 / PySide6（Nuke 内置 / built-in）

## License

MIT
