"""
VERICOM DLP 3D Printer GUI - Main Page
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt

from styles.colors import Colors
from styles.fonts import Fonts
from styles.icons import Icons
from components.icon_button import MainMenuButton


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
        
        # 상단 타이틀 영역
        title_widget = QWidget()
        title_widget.setFixedHeight(80)
        title_widget.setStyleSheet(f"background-color: {Colors.BG_SECONDARY};")
        
        title_layout = QVBoxLayout(title_widget)
        title_layout.setAlignment(Qt.AlignCenter)
        
        title_label = QLabel("VERICOM DLP Printer")
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
