"""
VERICOM DLP 3D Printer GUI - Icon Button Components
"""

from PySide6.QtWidgets import QPushButton, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap

from styles.colors import Colors
from styles.icons import Icons
from styles.stylesheets import (
    get_icon_button_style, get_icon_button_active_style,
    get_button_control_style, get_button_home_style,
    get_tool_button_style, get_tool_button_danger_style, get_main_menu_button_style
)


class IconButton(QPushButton):
    """기본 아이콘 버튼"""
    
    def __init__(self, icon_svg: str = None, size: int = 60, 
                 icon_size: int = 24, color: str = None, parent=None):
        super().__init__(parent)
        
        self._icon_svg = icon_svg
        self._icon_size = icon_size
        self._color = color or Colors.NAVY
        self._is_active = False
        
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(get_icon_button_style())

        if icon_svg:
            self._update_icon()
    
    def _update_icon(self):
        """아이콘 업데이트"""
        if self._icon_svg:
            icon = Icons.get_icon(self._icon_svg, self._icon_size, self._color)
            self.setIcon(icon)
            self.setIconSize(QSize(self._icon_size, self._icon_size))
    
    def set_icon(self, icon_svg: str, color: str = None):
        """아이콘 변경"""
        self._icon_svg = icon_svg
        if color:
            self._color = color
        self._update_icon()
    
    def set_active(self, active: bool):
        """활성 상태 설정"""
        self._is_active = active
        if active:
            self.setStyleSheet(get_icon_button_active_style())
            self._color = Colors.CYAN
        else:
            self.setStyleSheet(get_icon_button_style())
            self._color = Colors.NAVY
        self._update_icon()


class ControlButton(IconButton):
    """방향 제어용 버튼 (네이비 테두리)"""

    def __init__(self, icon_svg: str = None, size: int = 70,
                 icon_size: int = 28, parent=None):
        super().__init__(icon_svg, size, icon_size, Colors.NAVY, parent)
        self.setStyleSheet(get_button_control_style())


class HomeButton(IconButton):
    """홈 버튼 (시안 테두리)"""

    def __init__(self, size: int = 70, icon_size: int = 28, parent=None):
        super().__init__(Icons.HOME, size, icon_size, Colors.CYAN, parent)
        self.setStyleSheet(get_button_home_style())


class MainMenuButton(QPushButton):
    """메인 메뉴 큰 버튼 (아이콘 + 텍스트)"""

    def __init__(self, text: str, icon_svg: str, parent=None):
        super().__init__(parent)

        self._text = text
        self._icon_svg = icon_svg

        self.setFixedSize(200, 200)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(get_main_menu_button_style())

        self._setup_content()

    def _setup_content(self):
        """버튼 내용 구성"""
        # 아이콘 설정
        icon = Icons.get_icon(self._icon_svg, 64, Colors.NAVY)
        self.setIcon(icon)
        self.setIconSize(QSize(64, 64))

        # 텍스트 설정
        self.setText(self._text)

        # 아이콘 위, 텍스트 아래 배치를 위한 스타일
        self.setStyleSheet(self.styleSheet() + """
            QPushButton {
                padding-top: 30px;
                padding-bottom: 20px;
            }
        """)


class ToolButton(QPushButton):
    """도구 메뉴 버튼 (아이콘 + 텍스트)"""

    def __init__(self, text: str, icon_svg: str, is_danger: bool = False,
                 parent=None):
        super().__init__(parent)

        self._text = text
        self._icon_svg = icon_svg
        self._is_danger = is_danger

        self.setCursor(Qt.PointingHandCursor)

        if is_danger:
            self.setStyleSheet(get_tool_button_danger_style())
            self._color = Colors.RED
        else:
            self.setStyleSheet(get_tool_button_style())
            self._color = Colors.NAVY

        self._setup_content()

    def _setup_content(self):
        """버튼 내용 구성"""
        # 아이콘 설정
        icon = Icons.get_icon(self._icon_svg, 40, self._color)
        self.setIcon(icon)
        self.setIconSize(QSize(40, 40))

        # 텍스트 설정
        self.setText(self._text)


class LabeledIconButton(QWidget):
    """아이콘 + 하단 레이블 버튼 위젯"""
    
    def __init__(self, text: str, icon_svg: str, button_size: int = 60,
                 icon_size: int = 24, color: str = None, parent=None):
        super().__init__(parent)
        
        self._color = color or Colors.NAVY
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)
        
        # 아이콘 버튼
        self.button = IconButton(icon_svg, button_size, icon_size, 
                                  self._color, self)
        
        # 레이블
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        
        layout.addWidget(self.button, alignment=Qt.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignCenter)
    
    @property
    def clicked(self):
        """버튼 클릭 시그널 프록시"""
        return self.button.clicked
