"""
VERICOM DLP 3D Printer GUI - Tool Page
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QDialog, QLabel, QPushButton
)
from PySide6.QtCore import Signal, Qt

from pages.base_page import BasePage
from components.icon_button import ToolButton
from styles.icons import Icons
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius


class SimpleAlert(QDialog):
    """간단한 알림 다이얼로그"""
    
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("알림")
        self.setFixedSize(300, 150)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: {Radius.LG}px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(20)
        
        # 메시지
        lbl = QLabel(message)
        lbl.setFont(Fonts.h3())
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            background-color: {Colors.BG_PRIMARY};
            border: none;
        """)
        layout.addWidget(lbl)
        
        # OK 버튼
        btn_ok = QPushButton("OK")
        btn_ok.setFixedSize(100, 40)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setFont(Fonts.body())
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.NAVY};
                border: none;
                border-radius: {Radius.MD}px;
                color: {Colors.WHITE};
            }}
            QPushButton:pressed {{
                background-color: {Colors.NAVY_LIGHT};
            }}
        """)
        btn_ok.clicked.connect(self.accept)
        
        layout.addWidget(btn_ok, alignment=Qt.AlignCenter)


class ToolPage(BasePage):
    """도구 메뉴 페이지"""

    # 페이지 전환 시그널
    go_manual = Signal()
    go_exposure = Signal()
    go_setting = Signal()

    def __init__(self, parent=None):
        super().__init__("Tool", show_back=True, parent=parent)
        self._setup_content()

    # 3x2 그리드 때의 버튼 크기 유지
    BUTTON_SIZE = (200, 200)

    def _setup_content(self):
        """콘텐츠 구성"""
        self.content_layout.addStretch(1)

        # 가로 나열 레이아웃
        row = QHBoxLayout()
        row.setSpacing(20)
        row.addStretch()

        # Manual 버튼
        self.btn_manual = ToolButton("Manual", Icons.MOVE)
        self.btn_manual.setFixedSize(*self.BUTTON_SIZE)
        self.btn_manual.clicked.connect(self.go_manual.emit)
        row.addWidget(self.btn_manual)

        # Exposure 버튼
        self.btn_exposure = ToolButton("Exposure", Icons.SQUARE)
        self.btn_exposure.setFixedSize(*self.BUTTON_SIZE)
        self.btn_exposure.clicked.connect(self.go_exposure.emit)
        row.addWidget(self.btn_exposure)

        # Setting 버튼
        self.btn_setting = ToolButton("Setting", Icons.CALIBRATION)
        self.btn_setting.setFixedSize(*self.BUTTON_SIZE)
        self.btn_setting.clicked.connect(self.go_setting.emit)
        row.addWidget(self.btn_setting)

        row.addStretch()
        self.content_layout.addLayout(row)
        self.content_layout.addStretch(2)

