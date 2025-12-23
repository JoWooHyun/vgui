"""
VERICOM DLP 3D Printer GUI - Service Page
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt

from pages.base_page import BasePage
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius


class ServiceRow(QFrame):
    """서비스 정보 행 위젯"""
    
    def __init__(self, label: str, value: str, parent=None):
        super().__init__(parent)
        
        self.setFixedHeight(50)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: none;
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # 라벨
        lbl_label = QLabel(label)
        lbl_label.setFixedWidth(180)
        lbl_label.setFont(Fonts.body())
        lbl_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            background-color: {Colors.BG_SECONDARY};
            border: none;
        """)
        
        # 값 (링크 스타일)
        lbl_value = QLabel(value)
        lbl_value.setFont(Fonts.body())
        lbl_value.setStyleSheet(f"""
            color: {Colors.CYAN};
            background-color: {Colors.BG_SECONDARY};
            border: none;
        """)
        
        layout.addWidget(lbl_label)
        layout.addWidget(lbl_value)
        layout.addStretch()


class ServicePage(BasePage):
    """서비스 정보 페이지"""
    
    def __init__(self, parent=None):
        super().__init__("Service", show_back=True, parent=parent)
        
        # 서비스 정보
        self._info = {
            "Email": "vericom@vericom.co.kr",
            "Website": "www.vericom.co.kr",
            "Tel": "1661-2883",
        }
        
        self._setup_content()
    
    def _setup_content(self):
        """콘텐츠 구성"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(40, 20, 40, 20)
        
        # 테이블 컨테이너
        table_frame = QFrame()
        table_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: {Radius.MD}px;
            }}
        """)
        
        table_layout = QVBoxLayout(table_frame)
        table_layout.setSpacing(0)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # 헤더 행
        header = QFrame()
        header.setFixedHeight(45)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_TERTIARY};
                border: none;
                border-bottom: 1px solid {Colors.BORDER};
                border-top-left-radius: {Radius.MD}px;
                border-top-right-radius: {Radius.MD}px;
            }}
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        lbl_item = QLabel("항목")
        lbl_item.setFixedWidth(180)
        lbl_item.setFont(Fonts.body())
        lbl_item.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            background-color: {Colors.BG_TERTIARY};
            border: none;
            font-weight: 600;
        """)
        
        lbl_value = QLabel("정보")
        lbl_value.setFont(Fonts.body())
        lbl_value.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            background-color: {Colors.BG_TERTIARY};
            border: none;
            font-weight: 600;
        """)
        
        header_layout.addWidget(lbl_item)
        header_layout.addWidget(lbl_value)
        header_layout.addStretch()
        
        table_layout.addWidget(header)
        
        # 정보 행들
        for label, value in self._info.items():
            row = ServiceRow(label, value)
            table_layout.addWidget(row)
        
        table_layout.addStretch()
        
        main_layout.addWidget(table_frame)
        main_layout.addStretch()
        
        self.content_layout.addLayout(main_layout)
