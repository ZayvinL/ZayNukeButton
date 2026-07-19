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
# from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QCheckBox
# from PySide6.QtCore import Qt, Signal
# from PySide6.QtGui import QPixmap

from qt_imports import QWidget, QHBoxLayout, QLabel, QCheckBox, Qt, Signal, QPixmap

import paths_setup as psp


class ToolItemWidget(QWidget):
    """自定义工具列表项"""
    stateChanged = Signal()
    
    def __init__(self, tool_data, parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        self.setup_ui()
        self.load_icon()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # 安装复选框
        self.check_install = QCheckBox()
        self.check_install.setChecked(self.tool_data.get('is_installed', 0) == 1)
        self.check_install.stateChanged.connect(self.on_install_changed)
        layout.addWidget(self.check_install)
        
        # 收藏复选框
        self.check_favorite = QCheckBox()
        self.check_favorite.setChecked(self.tool_data.get('is_favorite', 0) == 1)
        self.check_favorite.stateChanged.connect(self.on_favorite_changed)
        layout.addWidget(self.check_favorite)
        
        # 图标标签
        self.lbl_icon = QLabel()
        self.lbl_icon.setFixedSize(24, 24)
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_icon)
        
        # 工具名称
        self.lbl_name = QLabel(self.tool_data.get('name', 'Unnamed'))
        layout.addWidget(self.lbl_name, 1)
    
    def load_icon(self):
        """加载工具图标"""
        icon_file = self.tool_data.get('icon_file')
        
        if icon_file:
            # 有图标，加载图片
            tools_root = psp.tools_path_get()
            icon_path = os.path.join(tools_root, icon_file.replace('/', os.sep))
            
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.lbl_icon.setPixmap(scaled_pixmap)
                    self.lbl_icon.setStyleSheet("")
                    return
        
        # 没有图标，显示纯色方块占位
        self.lbl_icon.setText("")
        self.lbl_icon.setStyleSheet("""
            QLabel {
                background-color: #555;
                border-radius: 4px;
            }
        """)
    
    def on_install_changed(self, state):
        """安装状态改变时，直接更新 tool_data"""
        new_value = 1 if state == Qt.CheckState.Checked else 0
        self.tool_data['is_installed'] = new_value
        self.stateChanged.emit()
    
    def on_favorite_changed(self, state):
        """收藏状态改变时，直接更新 tool_data"""
        new_value = 1 if state == Qt.CheckState.Checked else 0
        self.tool_data['is_favorite'] = new_value
        self.stateChanged.emit()