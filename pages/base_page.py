"""
VERICOM DLP 3D Printer GUI - Base Page Class
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from components.header import Header
from styles.colors import Colors


class BasePage(QWidget):
    """모든 페이지의 기본 클래스"""
    
    # 페이지 전환 시그널
    go_back = Signal()
    go_home = Signal()
    
    def __init__(self, title: str = "", show_back: bool = True, parent=None):
        super().__init__(parent)
        
        self._title = title
        self._show_back = show_back
        
        self._setup_base_ui()
    
    def _setup_base_ui(self):
        """기본 UI 구조 설정"""
        self.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")
        
        # 메인 레이아웃
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 헤더
        self.header = Header(self._title, self._show_back, self)
        self.header.back_clicked.connect(self._on_back_clicked)
        self.main_layout.addWidget(self.header)
        
        # 콘텐츠 영역
        self.content = QWidget()
        self.content.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(16)
        
        self.main_layout.addWidget(self.content, 1)
    
    def _on_back_clicked(self):
        """뒤로가기 처리"""
        self.go_back.emit()
    
    def set_title(self, title: str):
        """타이틀 변경"""
        self._title = title
        self.header.set_title(title)
