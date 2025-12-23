"""
VERICOM DLP 3D Printer GUI - Setting Page
LED Power 및 Blade 설정 페이지
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
)
from PySide6.QtCore import Signal, Qt

from pages.base_page import BasePage
from components.icon_button import ControlButton, HomeButton
from components.numeric_keypad import NumericKeypad
from styles.colors import Colors
from styles.fonts import Fonts
from styles.icons import Icons
from styles.stylesheets import (
    AXIS_PANEL_STYLE, AXIS_TITLE_STYLE,
    Radius
)


class LEDPowerPanel(QFrame):
    """LED Power 설정 패널"""

    power_changed = Signal(int)  # 파워 값 변경
    led_on = Signal()            # LED ON
    led_off = Signal()           # LED OFF

    def __init__(self, parent=None):
        super().__init__(parent)

        self._power_value = 100  # 기본값 100%
        self._is_on = False

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        self.setStyleSheet(AXIS_PANEL_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 타이틀
        self.title_label = QLabel("LED POWER SET")
        self.title_label.setStyleSheet(AXIS_TITLE_STYLE)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addStretch(1)

        # 파워 값 표시 (클릭 가능)
        self.power_btn = QPushButton(f"{self._power_value}%")
        self.power_btn.setFixedSize(200, 80)
        self.power_btn.setCursor(Qt.PointingHandCursor)
        self.power_btn.setFont(Fonts.mono_display())
        self.power_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_PRIMARY};
                border: 2px solid {Colors.CYAN};
                border-radius: {Radius.LG}px;
                color: {Colors.NAVY};
                font-size: 36px;
                font-weight: 700;
            }}
            QPushButton:pressed {{
                background-color: {Colors.BG_SECONDARY};
            }}
        """)
        self.power_btn.clicked.connect(self._on_power_click)

        power_container = QHBoxLayout()
        power_container.addStretch()
        power_container.addWidget(self.power_btn)
        power_container.addStretch()
        layout.addLayout(power_container)

        layout.addStretch(1)

        # ON/OFF 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.setAlignment(Qt.AlignCenter)

        self.btn_on = QPushButton("ON")
        self.btn_on.setFixedSize(100, 50)
        self.btn_on.setCursor(Qt.PointingHandCursor)
        self.btn_on.setFont(Fonts.h3())
        self.btn_on.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.TEAL};
                border: none;
                border-radius: {Radius.MD}px;
                color: {Colors.WHITE};
                font-weight: 600;
            }}
            QPushButton:pressed {{
                background-color: #0D9488;
            }}
        """)
        self.btn_on.clicked.connect(self._on_led_on)

        self.btn_off = QPushButton("OFF")
        self.btn_off.setFixedSize(100, 50)
        self.btn_off.setCursor(Qt.PointingHandCursor)
        self.btn_off.setFont(Fonts.h3())
        self.btn_off.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.RED};
                border: none;
                border-radius: {Radius.MD}px;
                color: {Colors.WHITE};
                font-weight: 600;
            }}
            QPushButton:pressed {{
                background-color: #B91C1C;
            }}
        """)
        self.btn_off.clicked.connect(self._on_led_off)

        btn_layout.addWidget(self.btn_on)
        btn_layout.addWidget(self.btn_off)
        layout.addLayout(btn_layout)

        layout.addStretch(1)

    def _on_power_click(self):
        """파워 값 클릭 - 키패드 열기"""
        keypad = NumericKeypad(
            title="LED Power",
            initial_value=self._power_value,
            unit="%",
            min_value=0,
            max_value=100,
            parent=self.window()
        )

        if keypad.exec():
            self._power_value = int(keypad.get_value())
            self.power_btn.setText(f"{self._power_value}%")
            self.power_changed.emit(self._power_value)

    def _on_led_on(self):
        """LED ON"""
        self._is_on = True
        self.led_on.emit()

    def _on_led_off(self):
        """LED OFF"""
        self._is_on = False
        self.led_off.emit()

    def get_power(self) -> int:
        """현재 파워 값 반환"""
        return self._power_value

    def set_power(self, value: int):
        """파워 값 설정"""
        self._power_value = max(0, min(100, value))
        self.power_btn.setText(f"{self._power_value}%")


class BladePanel(QFrame):
    """Blade 설정 패널"""

    speed_changed = Signal(int)    # 속도 변경
    move_positive = Signal()       # 오른쪽 이동
    move_negative = Signal()       # 왼쪽 이동
    home_axis = Signal()           # 홈 이동

    def __init__(self, parent=None):
        super().__init__(parent)

        self._speed_value = 30  # 기본값 30 mm/s

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        self.setStyleSheet(AXIS_PANEL_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 타이틀
        self.title_label = QLabel("BLADE SET")
        self.title_label.setStyleSheet(AXIS_TITLE_STYLE)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addStretch(1)

        # Speed 라벨
        speed_label = QLabel("Speed")
        speed_label.setAlignment(Qt.AlignCenter)
        speed_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 14px;
            }}
        """)
        layout.addWidget(speed_label)

        # 속도 값 표시 (클릭 가능)
        self.speed_btn = QPushButton(f"{self._speed_value} mm/s")
        self.speed_btn.setFixedSize(200, 80)
        self.speed_btn.setCursor(Qt.PointingHandCursor)
        self.speed_btn.setFont(Fonts.mono_display())
        self.speed_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_PRIMARY};
                border: 2px solid {Colors.CYAN};
                border-radius: {Radius.LG}px;
                color: {Colors.NAVY};
                font-size: 28px;
                font-weight: 700;
            }}
            QPushButton:pressed {{
                background-color: {Colors.BG_SECONDARY};
            }}
        """)
        self.speed_btn.clicked.connect(self._on_speed_click)

        speed_container = QHBoxLayout()
        speed_container.addStretch()
        speed_container.addWidget(self.speed_btn)
        speed_container.addStretch()
        layout.addLayout(speed_container)

        layout.addStretch(1)

        # 제어 버튼들 (홈, <, >)
        control_layout = QHBoxLayout()
        control_layout.setSpacing(12)
        control_layout.setAlignment(Qt.AlignCenter)

        # 홈 버튼
        self.btn_home = HomeButton(70, 28)
        self.btn_home.clicked.connect(self.home_axis.emit)

        # 왼쪽 버튼
        self.btn_left = ControlButton(Icons.CHEVRON_LEFT, 70, 28)
        self.btn_left.clicked.connect(self.move_negative.emit)

        # 오른쪽 버튼
        self.btn_right = ControlButton(Icons.CHEVRON_RIGHT, 70, 28)
        self.btn_right.clicked.connect(self.move_positive.emit)

        control_layout.addWidget(self.btn_home)
        control_layout.addWidget(self.btn_left)
        control_layout.addWidget(self.btn_right)

        layout.addLayout(control_layout)

        layout.addStretch(1)

    def _on_speed_click(self):
        """속도 값 클릭 - 키패드 열기"""
        keypad = NumericKeypad(
            title="Blade Speed",
            initial_value=self._speed_value,
            unit="mm/s",
            min_value=1,
            max_value=100,
            parent=self.window()
        )

        if keypad.exec():
            self._speed_value = int(keypad.get_value())
            self.speed_btn.setText(f"{self._speed_value} mm/s")
            self.speed_changed.emit(self._speed_value)

    def get_speed(self) -> int:
        """현재 속도 값 반환"""
        return self._speed_value

    def set_speed(self, value: int):
        """속도 값 설정"""
        self._speed_value = max(1, min(100, value))
        self.speed_btn.setText(f"{self._speed_value} mm/s")


class SettingPage(BasePage):
    """설정 페이지 (LED Power + Blade)"""

    # LED 시그널
    led_power_changed = Signal(int)
    led_on = Signal()
    led_off = Signal()

    # Blade 시그널
    blade_speed_changed = Signal(int)
    blade_move_positive = Signal()
    blade_move_negative = Signal()
    blade_home = Signal()

    def __init__(self, parent=None):
        super().__init__("Setting", show_back=True, parent=parent)
        self._setup_content()

    def _setup_content(self):
        """콘텐츠 구성"""
        # 2열 레이아웃
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(20)

        # LED Power 패널
        self.led_panel = LEDPowerPanel()
        self.led_panel.power_changed.connect(self.led_power_changed.emit)
        self.led_panel.led_on.connect(self.led_on.emit)
        self.led_panel.led_off.connect(self.led_off.emit)

        # Blade 패널
        self.blade_panel = BladePanel()
        self.blade_panel.speed_changed.connect(self.blade_speed_changed.emit)
        self.blade_panel.move_positive.connect(self.blade_move_positive.emit)
        self.blade_panel.move_negative.connect(self.blade_move_negative.emit)
        self.blade_panel.home_axis.connect(self.blade_home.emit)

        panels_layout.addWidget(self.led_panel)
        panels_layout.addWidget(self.blade_panel)

        self.content_layout.addLayout(panels_layout)

    def get_led_power(self) -> int:
        """LED 파워 값 반환"""
        return self.led_panel.get_power()

    def set_led_power(self, value: int):
        """LED 파워 값 설정"""
        self.led_panel.set_power(value)

    def get_blade_speed(self) -> int:
        """Blade 속도 값 반환"""
        return self.blade_panel.get_speed()

    def set_blade_speed(self, value: int):
        """Blade 속도 값 설정"""
        self.blade_panel.set_speed(value)
