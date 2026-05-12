# -*- coding: UTF-8 -*-
"""UI 组件"""

import os
import urllib.parse

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout

from window_01.config import _get_user_db_path, _get_toolbox_path

class ToolButton(QWidget):
    """自定义工具按钮"""
    
    clicked = Signal(object)  # 点击信号，传递按钮自身
    
    def __init__(self, tool_data, toolbox_path="", parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        # self.toolbox_path = toolbox_path
        self.toolbox_path = _get_toolbox_path()
        self._is_hovered = False
        self._setup_ui()
    
    def _setup_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        
        # 文字标签（支持自动换行）
        name = self.tool_data['tname']
        if '.' in name:
            name = name[:name.rindex('.')]
        
        self.text_label = QLabel(name)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)  # 启用自动换行
        self.text_label.setTextInteractionFlags(Qt.NoTextInteraction)
        
        layout.addWidget(self.text_label)
        
        # 构建 tooltip（包含图标）
        tooltip_parts = [
            f"<b>工具名称:</b> {self.tool_data['tname']}",
            f"<b>说明:</b> {self.tool_data['ttip']}",
            f"<b>类:</b> {self.tool_data['tclass']}"
        ]
        
        # 拼接工具路径
        if self.tool_data['tpath']:
            tool_path = self.tool_data['tpath']
            if self.toolbox_path and not os.path.isabs(tool_path):
                tool_path = os.path.join(self.toolbox_path, tool_path)
            tooltip_parts.append(f"<b>路径:</b> {tool_path}")
        
        # 添加图标
        if self.tool_data['tpng']:
            icon_path = self.tool_data['tpng']
            icon_path = os.path.join(self.toolbox_path, icon_path)
            if os.path.exists(icon_path):
                # 使用 urllib.parse.quote 编码路径
                ed_image_path = urllib.parse.quote(icon_path, safe='')
                tooltip_parts.append(f'<img src="{ed_image_path}" width="350">')
            else:
                tooltip_parts.append(f"<b>图标路径:</b> {icon_path} (文件不存在)")
        
        if self.tool_data['is_favorite']:
            tooltip_parts.append("⭐ 已收藏")
        
        # 使用完整的 HTML 文档格式
        tooltip_html = "<html><body><p>" + "</p><p>".join(tooltip_parts) + "</p></body></html>"
        #print(f"  完整tooltip: {tooltip_html}")
        self.setToolTip(tooltip_html)
        
        # 应用初始样式
        self._update_style()
        
        # 从属性获取固定大小
        width = self.property('button_width') or 150
        height = self.property('button_height') or 70
        self.setFixedSize(width, height)
    
    def _update_style(self):
        """更新样式"""
        if self._is_hovered:
            bg_color = "rgba(50, 60, 70, 255)"
            border_color = "rgba(100, 130, 160, 250)"
            text_color = "rgba(255, 200, 100, 255)"
        else:
            bg_color = "rgba(50, 60, 70, 100)"
            border_color = "rgba(80, 100, 120, 150)"
            text_color = "rgba(200, 210, 220, 255)"
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 5px;
            }}
            QLabel {{
                color: {text_color};
                font-size: 11px;
                background-color: {bg_color};
            }}
        """)
    
    def update_content(self, tool_data):
        """更新按钮内容（虚拟列表专用，不重建布局）"""
        self.tool_data = tool_data
        
        # 更新文字
        name = tool_data['tname']
        if '.' in name:
            name = name[:name.rindex('.')]
        
        self.text_label.setText(name)
        
        # 更新 tooltip
        tooltip_parts = [
            f"<b>工具名称:</b> {tool_data['tname']}",
            f"<b>说明:</b> {tool_data['ttip']}",
            f"<b>类:</b> {tool_data['tclass']}"
        ]
        
        if tool_data['tpath']:
            tool_path = tool_data['tpath']
            if self.toolbox_path and not os.path.isabs(tool_path):
                tool_path = os.path.join(self.toolbox_path, tool_path)
            tooltip_parts.append(f"<b>路径:</b> {tool_path}")
        
        if tool_data['tpng']:
            icon_path = tool_data['tpng']
            icon_path = os.path.join(self.toolbox_path, icon_path)
            if os.path.exists(icon_path):
                ed_image_path = urllib.parse.quote(icon_path, safe='')
                tooltip_parts.append(f'<img src="{ed_image_path}" width="350">')
            else:
                tooltip_parts.append(f"<b>图标路径:</b> {icon_path} (文件不存在)")
        
        if tool_data['is_favorite']:
            tooltip_parts.append("⭐ 已收藏")
        
        tooltip_html = "<html><body><p>" + "</p><p>".join(tooltip_parts) + "</p></body></html>"
        self.setToolTip(tooltip_html)
        
        # 重新应用样式，确保悬停状态正确显示
        self._update_style()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 发射点击信号
            self.clicked.emit(self)
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self._is_hovered = True
        self._update_style()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self._is_hovered = False
        self._update_style()
        super().leaveEvent(event)