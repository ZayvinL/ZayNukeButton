"""统一的 Qt 导入管理 - 兼容 PySide6 和 PySide2"""

import sys

# 检测并导入可用的 Qt 框架
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QMessageBox,
        QVBoxLayout, QHBoxLayout, QGridLayout, QListWidget,
        QListWidgetItem, QLabel, QPushButton, QLineEdit,
        QSplitter, QCheckBox, QGroupBox, QFormLayout,
        QTabWidget, QTextEdit, QTextBrowser, QScrollArea,
        QSizePolicy, QComboBox, QFileDialog, QSlider
    )
    from PySide6.QtCore import (
        Qt, QTimer, QEvent, Signal, QUrl, QSize, QSettings
    )
    from PySide6.QtGui import (
        QFont, QIcon, QPixmap, QClipboard, QImage,
        QKeySequence, QShortcut, QCursor
    )
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
            QSizePolicy, QComboBox, QFileDialog, QSlider
        )
        from PySide2.QtCore import (
            Qt, QTimer, QEvent, Signal, QUrl, QSize, QSettings
        )
        from PySide2.QtGui import (
            QFont, QIcon, QPixmap, QClipboard, QImage,
            QKeySequence, QCursor
        )
        
        # PySide2 中 QShortcut 在 QtWidgets 中
        from PySide2.QtWidgets import QShortcut
        
        from PySide2 import QtWidgets
        QT_VERSION = 5
        # print(f"✓ 使用 PySide2 (Qt {QT_VERSION})")
    except ImportError:
        raise ImportError("未找到 PySide6 或 PySide2，请安装其中一个")

# 导出所有需要的组件
__all__ = [
    # Widgets
    'QApplication', 'QMainWindow', 'QWidget', 'QMessageBox',
    'QVBoxLayout', 'QHBoxLayout', 'QGridLayout', 'QListWidget',
    'QListWidgetItem', 'QLabel', 'QPushButton', 'QLineEdit',
    'QSplitter', 'QCheckBox', 'QGroupBox', 'QFormLayout',
    'QTabWidget', 'QTextEdit', 'QTextBrowser', 'QScrollArea',
    'QSizePolicy', 'QComboBox', 'QFileDialog', 'QSlider', 'QShortcut',
    # Core
    'Qt', 'QTimer', 'QEvent', 'Signal', 'QUrl', 'QSize', 'QSettings',
    # Gui
    'QFont', 'QIcon', 'QPixmap', 'QClipboard', 'QImage',
    'QKeySequence', 'QCursor',
    # Module
    'QtWidgets',
    # Version
    'QT_VERSION'
]