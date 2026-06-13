from qt_imports import (Qt, QTimer, QEvent, Signal,
                        QMainWindow, QWidget, QVBoxLayout,
                        QHBoxLayout, QGridLayout, QScrollArea,
                        QLineEdit, QPushButton, QLabel, QMessageBox,
                        QSlider, QCheckBox, QKeySequence, QShortcut, QCursor,
                        QApplication)

def A_Toast(tile_info, message_info):
    global msg_box
    msg_box = QMessageBox()
    msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)
    msg_box.setText(f"{message_info}")
    msg_box.setWindowTitle(f"{tile_info}")
    msg_box.setIcon(QMessageBox.Information)
    timer = QTimer(msg_box)
    timer.singleShot(1300, msg_box.close)
    msg_box.setModal(False)
    msg_box.show()
    # 显示之后设置大小
    #msg_box.setFixedSize(1000, 200)

def B_Toast(title_info, message_info, duration_ms=1100):
    """用 QWidget+QLabel 实现的 Toast，支持按钮关闭、居中、自动换行"""
    global toast_win

    toast_win = QWidget()
    toast_win.setWindowFlags(
        Qt.FramelessWindowHint
        | Qt.WindowStaysOnTopHint
        | Qt.Tool
    )
    toast_win.setAttribute(Qt.WA_DeleteOnClose)
    toast_win.setStyleSheet("""
        QWidget#toast_bg {
            background: #2b2b2b;
            border: 1px solid #666;
            border-radius: 8px;
        }
    """)
    toast_win.setObjectName("toast_bg")

    layout = QVBoxLayout(toast_win)
    layout.setContentsMargins(24, 16, 24, 16)
    layout.setSpacing(12)

    # 标题
    title_label = QLabel(f"<b>{title_info}</b>")
    title_label.setStyleSheet("color: #eee; font-size: 15px; border: none;")
    title_label.setWordWrap(True)
    layout.addWidget(title_label)

    # 消息内容，支持自动换行
    msg_label = QLabel(message_info)
    msg_label.setStyleSheet("color: #ccc; font-size: 13px; border: none;")
    msg_label.setWordWrap(True)
    msg_label.setMaximumWidth(420)
    layout.addWidget(msg_label)

    # 关闭按钮
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    close_btn = QPushButton("确定")
    close_btn.setStyleSheet("""
        QPushButton {
            background: #555;
            color: #eee;
            padding: 6px 24px;
            border: none;
            border-radius: 4px;
            font-size: 13px;
        }
        QPushButton:hover {
            background: #777;
        }
    """)
    close_btn.clicked.connect(toast_win.close)
    btn_layout.addWidget(close_btn)
    layout.addLayout(btn_layout)

    # 先计算尺寸再居中
    toast_win.adjustSize()
    screen_center = toast_win.screen().availableGeometry().center()
    toast_win.move(
        screen_center.x() - toast_win.width() // 2,
        screen_center.y() - toast_win.height() // 2,
    )

    toast_win.show()

    # 自动关闭定时器（duration_ms=0 则不自动关闭）
    if duration_ms > 0:
        QTimer.singleShot(duration_ms, toast_win.close)
