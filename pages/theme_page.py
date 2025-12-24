"""
VERICOM DLP 3D Printer GUI - Theme Page
Light / Dark 테마 선택
"""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal

from pages.base_page import BasePage
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius
from controllers.theme_manager import get_theme_manager


class ThemeButton(QPushButton):
    """테마 선택 버튼 - 텍스트만"""

    def __init__(self, theme_name: str, display_name: str, parent=None):
        super().__init__(parent)

        self._theme_name = theme_name
        self._display_name = display_name
        self._is_selected = False

        self.setFixedSize(160, 100)
        self.setCursor(Qt.PointingHandCursor)

        # 레이아웃
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignCenter)

        # 텍스트만
        self.text_label = QLabel(display_name)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setFont(Fonts.h3())
        layout.addWidget(self.text_label, alignment=Qt.AlignCenter)

        self._update_style()

    @property
    def theme_name(self) -> str:
        return self._theme_name

    def set_selected(self, selected: bool):
        """선택 상태 설정"""
        self._is_selected = selected
        self._update_style()

    def _update_style(self):
        """스타일 업데이트"""
        if self._is_selected:
            # 선택됨: Cyan 배경
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.CYAN};
                    border: 3px solid {Colors.CYAN};
                    border-radius: {Radius.MD}px;
                }}
            """)
            text_color = Colors.WHITE
        else:
            # 미선택: 테두리만
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_SECONDARY};
                    border: 2px solid {Colors.BORDER};
                    border-radius: {Radius.MD}px;
                }}
                QPushButton:hover {{
                    border: 2px solid {Colors.CYAN};
                }}
            """)
            text_color = Colors.TEXT_PRIMARY

        # 텍스트 색상 업데이트
        self.text_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                background-color: transparent;
                border: none;
            }}
        """)

    def mousePressEvent(self, event):
        """클릭 시 스타일"""
        if not self._is_selected:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.CYAN_LIGHT};
                    border: 2px solid {Colors.CYAN};
                    border-radius: {Radius.MD}px;
                }}
            """)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """클릭 해제"""
        self._update_style()
        super().mouseReleaseEvent(event)


class ThemePage(BasePage):
    """테마 설정 페이지"""

    theme_applied = Signal(str)  # 테마 적용 시그널

    def __init__(self, parent=None):
        super().__init__("Theme", show_back=True, parent=parent)
        self._theme_manager = get_theme_manager()
        self._buttons = {}
        self._setup_content()
        self._load_current_theme()

        # 테마 변경 시그널 연결
        self._theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_content(self):
        """콘텐츠 구성"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 20, 40, 30)

        # 상단 여백
        main_layout.addStretch(1)

        # 설명 텍스트
        desc_label = QLabel("Select a theme")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setFont(Fonts.body())
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                background-color: transparent;
                border: none;
            }}
        """)
        main_layout.addWidget(desc_label)

        # 테마 버튼들
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        # Light 테마
        self.btn_light = ThemeButton("Light", "Light")
        self.btn_light.clicked.connect(lambda: self._select_theme("Light"))
        self._buttons["Light"] = self.btn_light

        # Dark 테마
        self.btn_dark = ThemeButton("Dark", "Dark")
        self.btn_dark.clicked.connect(lambda: self._select_theme("Dark"))
        self._buttons["Dark"] = self.btn_dark

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_light)
        btn_layout.addWidget(self.btn_dark)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)

        # 하단 여백
        main_layout.addStretch(2)

        self.content_layout.addLayout(main_layout)

    def _load_current_theme(self):
        """현재 테마 상태 로드"""
        current = self._theme_manager.current_theme
        self._update_button_states(current)

    def _select_theme(self, theme_name: str):
        """테마 선택"""
        self._theme_manager.set_theme(theme_name)
        self._update_button_states(theme_name)
        self.theme_applied.emit(theme_name)

    def _update_button_states(self, selected_theme: str):
        """버튼 상태 업데이트"""
        for name, btn in self._buttons.items():
            btn.set_selected(name == selected_theme)

    def _on_theme_changed(self, theme_name: str):
        """외부에서 테마 변경 시"""
        self._update_button_states(theme_name)
