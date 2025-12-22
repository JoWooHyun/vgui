"""
VERICOM DLP 3D Printer GUI - Main Page
"""

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap

from styles.colors import Colors
from styles.fonts import Fonts
from styles.icons import Icons
from components.icon_button import MainMenuButton

# 로고 경로
LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "VERICOM_LOGO.png")


class MainPage(QWidget):
    """메인 홈 페이지"""
    
    # 페이지 전환 시그널
    go_tool = Signal()
    go_system = Signal()
    go_print = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI 구성"""
        self.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 상단 로고 영역
        logo_widget = QWidget()
        logo_widget.setFixedHeight(100)
        logo_widget.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")

        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setAlignment(Qt.AlignCenter)

        # 로고 이미지
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(LOGO_PATH):
            pixmap = QPixmap(LOGO_PATH)
            # 너비 280px 기준으로 비율 유지하며 스케일
            scaled_pixmap = pixmap.scaledToWidth(280, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            # 로고 파일 없으면 텍스트 표시
            logo_label.setText("VERICOM DLP Printer")
            logo_label.setFont(Fonts.h3())
            logo_label.setStyleSheet(f"color: {Colors.NAVY};")

        logo_layout.addWidget(logo_label)
        layout.addWidget(logo_widget)
        
        # 메인 콘텐츠 영역
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setSpacing(32)
        
        # Tool 버튼
        self.btn_tool = MainMenuButton("Tool", Icons.WRENCH)
        self.btn_tool.clicked.connect(self.go_tool.emit)
        
        # System 버튼
        self.btn_system = MainMenuButton("System", Icons.SETTINGS)
        self.btn_system.clicked.connect(self.go_system.emit)
        
        # Print 버튼
        self.btn_print = MainMenuButton("Print", Icons.LAYERS)
        self.btn_print.clicked.connect(self.go_print.emit)
        
        content_layout.addWidget(self.btn_tool)
        content_layout.addWidget(self.btn_system)
        content_layout.addWidget(self.btn_print)
        
        layout.addWidget(content, 1)
