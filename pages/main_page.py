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


class ClickableLabel(QLabel):
    """클릭 가능한 QLabel"""
    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class MainPage(QWidget):
    """메인 홈 페이지"""
    
    # 페이지 전환 시그널
    go_tool = Signal()
    go_system = Signal()
    go_print = Signal()
    logo_clicked = Signal()  # 로고 클릭 시그널 (관리자 모드용)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI 구성"""
        self.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 상단 타이틀 영역
        title_widget = QWidget()
        title_widget.setFixedHeight(80)
        title_widget.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")

        title_layout = QVBoxLayout(title_widget)
        title_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("MAZIC CERA")
        title_label.setFont(Fonts.h3())
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {Colors.NAVY};")

        title_layout.addWidget(title_label)
        layout.addWidget(title_widget)
        
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

        # 우측 하단 로고
        footer_widget = QWidget()
        footer_widget.setFixedHeight(44)
        footer_widget.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")

        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 0, 16, 8)

        footer_layout.addStretch()

        # 소형 로고 (클릭 가능 - 관리자 모드용)
        self.logo_btn = ClickableLabel()
        if os.path.exists(LOGO_PATH):
            pixmap = QPixmap(LOGO_PATH)
            scaled_pixmap = pixmap.scaledToWidth(88, Qt.SmoothTransformation)
            self.logo_btn.setPixmap(scaled_pixmap)
        self.logo_btn.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")
        self.logo_btn.clicked.connect(self.logo_clicked.emit)

        footer_layout.addWidget(self.logo_btn)

        layout.addWidget(footer_widget)
