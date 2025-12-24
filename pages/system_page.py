"""
VERICOM DLP 3D Printer GUI - System Page
"""

from PySide6.QtWidgets import QGridLayout, QDialog, QVBoxLayout, QLabel, QPushButton
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


class SystemPage(BasePage):
    """시스템 설정 페이지"""
    
    # 페이지 전환 시그널
    go_device_info = Signal()
    go_language = Signal()
    go_service = Signal()
    go_theme = Signal()
    
    def __init__(self, parent=None):
        super().__init__("System", show_back=True, parent=parent)
        self._setup_content()
    
    def _setup_content(self):
        """콘텐츠 구성"""
        # 그리드 레이아웃 (3×2) - tool_page.py와 동일
        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setContentsMargins(40, 10, 40, 10)

        # Device Info 버튼
        self.btn_device = ToolButton("Device Info", Icons.INFO)
        self.btn_device.clicked.connect(self.go_device_info.emit)

        # Language 버튼
        self.btn_language = ToolButton("Language", Icons.GLOBE)
        self.btn_language.clicked.connect(self.go_language.emit)

        # Service 버튼
        self.btn_service = ToolButton("Service", Icons.MAIL)
        self.btn_service.clicked.connect(self.go_service.emit)

        # Network 버튼 (알림창)
        self.btn_network = ToolButton("Network", Icons.WIFI)
        self.btn_network.clicked.connect(self._on_network)

        # Theme 버튼
        self.btn_theme = ToolButton("Theme", Icons.SUN)
        self.btn_theme.clicked.connect(self.go_theme.emit)

        # Back 버튼
        self.btn_back = ToolButton("Back", Icons.ARROW_LEFT)
        self.btn_back.clicked.connect(self.go_back.emit)

        # 그리드에 배치 (3×2) - tool_page.py와 동일 배치
        grid.addWidget(self.btn_device, 0, 0)
        grid.addWidget(self.btn_language, 0, 1)
        grid.addWidget(self.btn_service, 0, 2)
        grid.addWidget(self.btn_network, 1, 0)
        grid.addWidget(self.btn_theme, 1, 1)
        grid.addWidget(self.btn_back, 1, 2)

        # 모든 버튼 크기 동일하게 (tool_page.py와 동일: 140)
        for i in range(grid.count()):
            widget = grid.itemAt(i).widget()
            if widget:
                widget.setMinimumHeight(140)

        self.content_layout.addLayout(grid)
    
    def _on_network(self):
        """Network 버튼 클릭 - 알림창"""
        alert = SimpleAlert("구현중입니다", self)
        alert.exec()
