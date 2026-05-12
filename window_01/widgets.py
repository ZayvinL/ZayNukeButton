# c:/Users/liucx/.nuke/MyButton/window_01/widgets.py
# -*- coding: UTF-8 -*-
"""UI 组件"""

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QPushButton


class ToolButton(QPushButton):
    """自定义工具按钮"""
    
    def __init__(self, tool_data, parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        self._setup_ui()
    
    def _setup_ui(self):
        name = self.tool_data['tname']
        if '.' in name:
            name = name[:name.rindex('.')]
        
        # 不截断名称，让文字在按钮内显示
        self.setText(name)
        
        # 构建 tooltip
        tooltip_parts = [f"<b>{self.tool_data['tname']}</b>"]
        if self.tool_data['ttip']:
            tooltip_parts.append(f"说明: {self.tool_data['ttip']}")
        if self.tool_data['tclass']:
            tooltip_parts.append(f"类: {self.tool_data['tclass']}")
        if self.tool_data['is_favorite']:
            tooltip_parts.append("⭐ 已收藏")
        
        self.setToolTip("<br>".join(tooltip_parts))
        
        self.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 5px;
                font-size: 11px;
                background-color: rgba(50, 60, 70, 200);
                color: rgba(200, 210, 220, 255);
                border: 1px solid rgba(80, 100, 120, 150);
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(70, 90, 110, 220);
                color: rgba(255, 200, 100, 255);
                border-color: rgba(100, 130, 160, 200);
            }
            QPushButton:pressed {
                background-color: rgba(60, 80, 100, 200);
            }
        """)
        
        # 从属性获取固定大小
        width = self.property('button_width') or 150
        height = self.property('button_height') or 70
        self.setFixedSize(width, height)
    
    def set_icon(self, icon):
        if not icon.isNull():
            self.setIcon(icon)
            self.setIconSize(QSize(20, 20))