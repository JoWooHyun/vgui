"""
VERICOM DLP 3D Printer GUI - Print Test Page
테스트 모드 설정 요약 + 레이어 수 입력 + Start 버튼
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QWidget, QLabel, QPushButton
)
from PySide6.QtCore import Signal, Qt

from pages.base_page import BasePage
from components.numeric_keypad import NumericKeypad
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius
from controllers.settings_manager import get_settings


class PrintTestPage(BasePage):
    """테스트 프린트 설정 및 시작 페이지"""

    start_test = Signal(dict)

    def __init__(self, parent=None):
        super().__init__("Print Test", show_back=True, parent=parent)
        self.settings = get_settings()
        self._total_layers = 10
        self._layer_height = 0.05
        self._bottom_layers = 3
        self._setup_content()

    def _setup_content(self):
        self.content_layout.setContentsMargins(20, 10, 20, 10)

        main_row = QHBoxLayout()
        main_row.setSpacing(20)

        # === 좌측: 현재 설정 요약 ===
        left_panel = QWidget()
        left_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.BG_SECONDARY};
                border-radius: {Radius.LG}px;
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 15, 20, 15)
        left_layout.setSpacing(8)

        lbl_title = QLabel("Test Settings")
        lbl_title.setFont(Fonts.h3())
        lbl_title.setStyleSheet(f"color: {Colors.AMBER}; background: transparent;")
        left_layout.addWidget(lbl_title)

        self.grid = QGridLayout()
        self.grid.setSpacing(6)
        self._labels = {}

        items = [
            ("Blade Spd 1", "blade_speed", "mm/s"),
            ("Blade Spd 2", "blade_speed2", "mm/s"),
            ("Boundary", "blade_boundary", "mm"),
            ("Dispense Dist", "y_dispense_dist", "mm"),
            ("Dispense Speed", "y_dispense_speed", "mm/s"),
            ("Dispense Delay", "y_dispense_delay", "s"),
            ("Pull Distance", "y_pull_dist", "mm"),
            ("Pull Delay", "y_pull_delay", "s"),
            ("Return Dist", "y_return_dist", "mm"),
            ("Return Delay", "y_return_delay", "s"),
            ("Priming Pos", "priming_pos", "mm"),
        ]

        for i, (label, key, unit) in enumerate(items):
            lbl_name = QLabel(f"{label}:")
            lbl_name.setFont(Fonts.body())
            lbl_name.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
            self.grid.addWidget(lbl_name, i, 0)

            lbl_value = QLabel("--")
            lbl_value.setFont(Fonts.body())
            lbl_value.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent; font-weight: bold;")
            self.grid.addWidget(lbl_value, i, 1)

            if unit:
                lbl_unit = QLabel(unit)
                lbl_unit.setFont(Fonts.caption())
                lbl_unit.setStyleSheet(f"color: {Colors.TEXT_DISABLED}; background: transparent;")
                self.grid.addWidget(lbl_unit, i, 2)

            self._labels[key] = lbl_value

        left_layout.addLayout(self.grid)
        left_layout.addStretch()
        main_row.addWidget(left_panel, 3)

        # === 우측: 레이어 설정 + Start ===
        right_panel = QWidget()
        right_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.BG_SECONDARY};
                border-radius: {Radius.LG}px;
            }}
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 15, 20, 15)
        right_layout.setSpacing(12)

        # 레이어 수
        row_layers = QHBoxLayout()
        lbl_layers = QLabel("Layers:")
        lbl_layers.setFont(Fonts.h3())
        lbl_layers.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        row_layers.addWidget(lbl_layers)

        self.lbl_layer_count = QLabel(str(self._total_layers))
        self.lbl_layer_count.setFont(Fonts.h2())
        self.lbl_layer_count.setAlignment(Qt.AlignCenter)
        self.lbl_layer_count.setStyleSheet(f"color: {Colors.AMBER}; background: transparent; font-weight: bold;")
        self.lbl_layer_count.mousePressEvent = lambda e: self._edit_value("layers")
        row_layers.addWidget(self.lbl_layer_count)
        right_layout.addLayout(row_layers)

        # 레이어 높이
        row_height = QHBoxLayout()
        lbl_h = QLabel("Layer Height:")
        lbl_h.setFont(Fonts.h3())
        lbl_h.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        row_height.addWidget(lbl_h)

        self.lbl_layer_height = QLabel(f"{self._layer_height} mm")
        self.lbl_layer_height.setFont(Fonts.h2())
        self.lbl_layer_height.setAlignment(Qt.AlignCenter)
        self.lbl_layer_height.setStyleSheet(f"color: {Colors.AMBER}; background: transparent; font-weight: bold;")
        self.lbl_layer_height.mousePressEvent = lambda e: self._edit_value("height")
        row_height.addWidget(self.lbl_layer_height)
        right_layout.addLayout(row_height)

        # 바닥 레이어
        row_bottom = QHBoxLayout()
        lbl_b = QLabel("Bottom Layers:")
        lbl_b.setFont(Fonts.h3())
        lbl_b.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        row_bottom.addWidget(lbl_b)

        self.lbl_bottom_layers = QLabel(str(self._bottom_layers))
        self.lbl_bottom_layers.setFont(Fonts.h2())
        self.lbl_bottom_layers.setAlignment(Qt.AlignCenter)
        self.lbl_bottom_layers.setStyleSheet(f"color: {Colors.AMBER}; background: transparent; font-weight: bold;")
        self.lbl_bottom_layers.mousePressEvent = lambda e: self._edit_value("bottom")
        row_bottom.addWidget(self.lbl_bottom_layers)
        right_layout.addLayout(row_bottom)

        right_layout.addStretch()

        # Start 버튼
        self.btn_start = QPushButton("START")
        self.btn_start.setFixedHeight(60)
        self.btn_start.setFont(Fonts.h2())
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.NAVY};
                border: none;
                border-radius: {Radius.LG}px;
                color: {Colors.WHITE};
                font-weight: bold;
            }}
            QPushButton:pressed {{ background-color: {Colors.NAVY_LIGHT}; }}
        """)
        self.btn_start.clicked.connect(self._on_start)
        right_layout.addWidget(self.btn_start)

        main_row.addWidget(right_panel, 2)
        self.content_layout.addLayout(main_row)

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_settings()

    def _refresh_settings(self):
        preset = self.settings.get_selected_test_material_preset()
        if preset:
            self._labels["blade_speed"].setText(str(preset.blade_speed))
            self._labels["blade_speed2"].setText(str(preset.blade_speed2))
            self._labels["blade_boundary"].setText(str(preset.blade_boundary))
            self._labels["y_dispense_dist"].setText(str(preset.y_dispense_distance))
            self._labels["y_dispense_speed"].setText(str(preset.y_dispense_speed))
            self._labels["y_dispense_delay"].setText(str(preset.y_dispense_delay))
            self._labels["y_pull_dist"].setText(str(preset.y_pull_distance))
            self._labels["y_pull_delay"].setText(str(preset.y_pull_delay))
            self._labels["y_return_dist"].setText(str(preset.y_return_distance))
            self._labels["y_return_delay"].setText(str(preset.y_return_delay))

        priming = self.settings.get_y_priming_position()
        self._labels["priming_pos"].setText(f"{priming:.1f}")

    def _edit_value(self, which: str):
        if which == "layers":
            keypad = NumericKeypad(
                title="Total Layers",
                value=self._total_layers,
                min_val=1, max_val=1000,
                allow_decimal=False,
                parent=self
            )
            if keypad.exec():
                self._total_layers = int(keypad.get_value())
                self.lbl_layer_count.setText(str(self._total_layers))
        elif which == "height":
            keypad = NumericKeypad(
                title="Layer Height (mm)",
                value=self._layer_height,
                min_val=0.01, max_val=1.0,
                allow_decimal=True,
                parent=self
            )
            if keypad.exec():
                self._layer_height = keypad.get_value()
                self.lbl_layer_height.setText(f"{self._layer_height} mm")
        elif which == "bottom":
            keypad = NumericKeypad(
                title="Bottom Layers",
                value=self._bottom_layers,
                min_val=0, max_val=20,
                allow_decimal=False,
                parent=self
            )
            if keypad.exec():
                self._bottom_layers = int(keypad.get_value())
                self.lbl_bottom_layers.setText(str(self._bottom_layers))

    def _on_start(self):
        preset = self.settings.get_selected_test_material_preset()

        params = {
            'totalLayer': self._total_layers,
            'layerHeight': self._layer_height,
            'bottomLayerCount': self._bottom_layers,
            'bladeSpeed': preset.blade_speed * 60 if preset else 300,
            'bladeSpeed2': preset.blade_speed2 * 60 if preset else 1200,
            'bladeBoundary': preset.blade_boundary if preset else 60.0,
            'bladeCycles': 1,
            'levelingCycles': 1,
            'yDispenseDistance': preset.y_dispense_distance if preset else 1.0,
            'yDispenseSpeed': preset.y_dispense_speed * 60 if preset else 180,
            'yDispenseDelay': preset.y_dispense_delay if preset else 2.0,
            'yPullDistance': preset.y_pull_distance if preset else 0.0,
            'yPullDelay': preset.y_pull_delay if preset else 2.0,
            'yReturnDistance': preset.y_return_distance if preset else 0.0,
            'yReturnDelay': preset.y_return_delay if preset else 2.0,
        }

        self.start_test.emit(params)
