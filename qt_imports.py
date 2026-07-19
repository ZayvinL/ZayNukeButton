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

"""统一的 Qt 导入管理 - 兼容 PySide6 和 PySide2"""

# 检测并导入可用的 Qt 框架
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QMessageBox,
        QVBoxLayout, QHBoxLayout, QGridLayout, QListWidget,
        QListWidgetItem, QLabel, QPushButton, QLineEdit,
        QSplitter, QCheckBox, QGroupBox, QFormLayout,
        QTabWidget, QTextEdit, QTextBrowser, QScrollArea,
        QSizePolicy, QComboBox, QFileDialog, QSlider,
        QMenu, QInputDialog, QTableWidget, QTableWidgetItem,
        QHeaderView, QAbstractItemView
    )
    from PySide6.QtCore import (
        Qt, QTimer, QEvent, Signal, QUrl, QSize, QSettings
    )
    from PySide6.QtGui import (
        QFont, QIcon, QPixmap, QClipboard, QImage,
        QKeySequence, QCursor, QDesktopServices, QMovie
    )

    # PySide6 中 QShortcut / QAction 在 QtGui 中
    from PySide6.QtGui import QShortcut, QAction

    from PySide6 import QtWidgets
    QT_VERSION = 6
    # print(f"✓ 使用 PySide6 (Qt {QT_VERSION})")
except ImportError:
    try:
        from PySide2.QtWidgets import (
            QApplication, QMainWindow, QWidget, QMessageBox,
            QVBoxLayout, QHBoxLayout, QGridLayout, QListWidget,
            QListWidgetItem, QLabel, QPushButton, QLineEdit,
            QSplitter, QCheckBox, QGroupBox, QFormLayout,
            QTabWidget, QTextEdit, QTextBrowser, QScrollArea,
            QSizePolicy, QComboBox, QFileDialog, QSlider,
            QMenu, QInputDialog, QTableWidget, QTableWidgetItem,
            QHeaderView, QAbstractItemView
        )
        from PySide2.QtCore import (
            Qt, QTimer, QEvent, Signal, QUrl, QSize, QSettings
        )
        from PySide2.QtGui import (
            QFont, QIcon, QPixmap, QClipboard, QImage,
            QKeySequence, QCursor, QDesktopServices, QMovie
        )

        # PySide2 中 QShortcut / QAction 在 QtWidgets 中
        from PySide2.QtWidgets import QShortcut, QAction

        from PySide2 import QtWidgets
        QT_VERSION = 5
        # print(f"✓ 使用 PySide2 (Qt {QT_VERSION})")
    except ImportError:
        raise ImportError("未找到 PySide6 或 PySide2，请安装其中一个")


def exec_dialog(dialog):
    """兼容 PySide2 5.12+ / PySide6 的对话框 exec 调用"""
    if hasattr(dialog, "exec"):
        return dialog.exec()
    return dialog.exec_()


# 导出所有需要的组件
__all__ = [
    # Widgets
    'QApplication', 'QMainWindow', 'QWidget', 'QMessageBox',
    'QVBoxLayout', 'QHBoxLayout', 'QGridLayout', 'QListWidget',
    'QListWidgetItem', 'QLabel', 'QPushButton', 'QLineEdit',
    'QSplitter', 'QCheckBox', 'QGroupBox', 'QFormLayout',
    'QTabWidget', 'QTextEdit', 'QTextBrowser', 'QScrollArea',
    'QSizePolicy', 'QComboBox', 'QFileDialog', 'QSlider',
    'QMenu', 'QInputDialog', 'QTableWidget', 'QTableWidgetItem',
    'QHeaderView', 'QAbstractItemView',
    # Core
    'Qt', 'QTimer', 'QEvent', 'Signal', 'QUrl', 'QSize', 'QSettings',
    # Gui
    'QFont', 'QIcon', 'QPixmap', 'QClipboard', 'QImage',
    'QKeySequence', 'QCursor', 'QDesktopServices', 'QMovie',
    # 版本分支类 (Qt5 在 QtWidgets, Qt6 在 QtGui)
    'QShortcut', 'QAction',
    # Module
    'QtWidgets',
    # Version
    'QT_VERSION',
    # Helper
    'exec_dialog',
]
