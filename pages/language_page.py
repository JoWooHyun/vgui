"""
VERICOM DLP 3D Printer GUI - Language Page
"""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt

from pages.base_page import BasePage
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius


class LanguageButton(QPushButton):
    """언어 선택 버튼"""

    def __init__(self, text: str, lang_name: str, parent=None):
        super().__init__(text, parent)

        self._lang_name = lang_name
        self.setFixedSize(100, 100)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(Fonts.h1())
        self._set_normal_style()

    def _set_normal_style(self):
        """기본 스타일"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                border: 2px solid {Colors.CYAN};
                border-radius: {Radius.MD}px;
                color: {Colors.CYAN};
                font-size: 32px;
                font-weight: bold;
            }}
        """)

    def _set_pressed_style(self):
        """눌렀을 때 스타일"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.CYAN};
                border: 2px solid {Colors.CYAN};
                border-radius: {Radius.MD}px;
                color: {Colors.WHITE};
                font-size: 32px;
                font-weight: bold;
            }}
        """)

    def mousePressEvent(self, event):
        self._set_pressed_style()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._set_normal_style()
        super().mouseReleaseEvent(event)


class LanguagePage(BasePage):
    """언어 설정 페이지"""

    def __init__(self, parent=None):
        super().__init__("Language", show_back=True, parent=parent)
        self._setup_content()

    def _setup_content(self):
        """콘텐츠 구성"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 20, 40, 30)

        # 상단 여백
        main_layout.addStretch(1)

        # 언어 버튼들
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        # 한국어
        self.btn_ko = LanguageButton("한", "한국어")
        # 중국어
        self.btn_zh = LanguageButton("中", "中文")
        # 일본어
        self.btn_ja = LanguageButton("日", "日本語")
        # 영어
        self.btn_en = LanguageButton("E", "English")

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ko)
        btn_layout.addWidget(self.btn_zh)
        btn_layout.addWidget(self.btn_ja)
        btn_layout.addWidget(self.btn_en)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)

        # 하단 여백
        main_layout.addStretch(2)

        self.content_layout.addLayout(main_layout)
