"""
VERICOM DLP 3D Printer GUI - Language Page
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Signal, Qt

from pages.base_page import BasePage
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius


class LanguageRow(QFrame):
    """언어 선택 행 위젯"""
    
    clicked = Signal(str)
    
    def __init__(self, lang_code: str, lang_name: str, lang_desc: str, parent=None):
        super().__init__(parent)
        
        self._lang_code = lang_code
        self._selected = False
        
        self.setFixedHeight(50)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # 언어 이름
        self.lbl_name = QLabel(lang_name)
        self.lbl_name.setFixedWidth(180)
        self.lbl_name.setFont(Fonts.body())
        
        # 설명
        self.lbl_desc = QLabel(lang_desc)
        self.lbl_desc.setFont(Fonts.body())
        
        layout.addWidget(self.lbl_name)
        layout.addWidget(self.lbl_desc)
        layout.addStretch()
        
        self._update_label_style()
    
    def _update_style(self):
        """선택 상태에 따른 스타일"""
        if self._selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.CYAN_ALPHA_10};
                    border: none;
                    border-bottom: 1px solid {Colors.BORDER};
                    border-left: 4px solid {Colors.CYAN};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {Colors.BG_SECONDARY};
                    border: none;
                    border-bottom: 1px solid {Colors.BORDER};
                }}
                QFrame:hover {{
                    background-color: {Colors.BG_TERTIARY};
                }}
            """)
    
    def _update_label_style(self):
        """라벨 스타일 업데이트"""
        bg_color = Colors.CYAN_ALPHA_10 if self._selected else Colors.BG_SECONDARY
        name_color = Colors.CYAN if self._selected else Colors.TEXT_SECONDARY
        desc_color = Colors.CYAN if self._selected else Colors.TEXT_PRIMARY
        
        self.lbl_name.setStyleSheet(f"""
            color: {name_color};
            background-color: transparent;
            border: none;
        """)
        self.lbl_desc.setStyleSheet(f"""
            color: {desc_color};
            background-color: transparent;
            border: none;
        """)
    
    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_style()
        self._update_label_style()
    
    def is_selected(self) -> bool:
        return self._selected
    
    def mousePressEvent(self, event):
        self.clicked.emit(self._lang_code)
        super().mousePressEvent(event)


class LanguagePage(BasePage):
    """언어 설정 페이지"""
    
    language_changed = Signal(str)  # "en" or "ko"
    
    def __init__(self, parent=None):
        super().__init__("Language", show_back=True, parent=parent)
        
        self._current_lang = "en"  # 기본값
        self._rows = {}
        
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
        
        lbl_desc = QLabel("설명")
        lbl_desc.setFont(Fonts.body())
        lbl_desc.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            background-color: {Colors.BG_TERTIARY};
            border: none;
            font-weight: 600;
        """)
        
        header_layout.addWidget(lbl_item)
        header_layout.addWidget(lbl_desc)
        header_layout.addStretch()
        
        table_layout.addWidget(header)
        
        # 언어 행들
        languages = [
            ("en", "English", "영어"),
            ("ko", "한국어", "한글"),
        ]
        
        for lang_code, lang_name, lang_desc in languages:
            row = LanguageRow(lang_code, lang_name, lang_desc)
            row.clicked.connect(self._on_language_clicked)
            self._rows[lang_code] = row
            table_layout.addWidget(row)
        
        # 기본 선택
        self._rows[self._current_lang].set_selected(True)
        
        table_layout.addStretch()
        
        main_layout.addWidget(table_frame)
        main_layout.addStretch()
        
        self.content_layout.addLayout(main_layout)
    
    def _on_language_clicked(self, lang_code: str):
        """언어 선택"""
        if lang_code == self._current_lang:
            return
        
        # 이전 선택 해제
        self._rows[self._current_lang].set_selected(False)
        
        # 새로운 선택
        self._current_lang = lang_code
        self._rows[lang_code].set_selected(True)
        
        # 시그널 발생
        self.language_changed.emit(lang_code)
    
    def get_current_language(self) -> str:
        return self._current_lang
    
    def set_language(self, lang_code: str):
        if lang_code in self._rows:
            self._on_language_clicked(lang_code)
