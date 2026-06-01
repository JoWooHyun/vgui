"""
VERICOM DLP 3D Printer GUI - Test Material Preset Page
테스트 모드 전용 소재 프리셋 관리 (프로덕션과 완전 분리)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QDialog, QLineEdit
)
from PySide6.QtCore import Signal, Qt

from pages.base_page import BasePage
from components.numeric_keypad import NumericKeypad
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius
from controllers.settings_manager import get_settings, TestMaterialPreset


class TestMaterialNameDialog(QDialog):
    """소재 이름 입력 다이얼로그"""

    def __init__(self, title: str = "New Material", current_name: str = "", parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(350, 180)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_PRIMARY};
                border: 2px solid {Colors.AMBER};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        lbl_title = QLabel(title)
        lbl_title.setFont(Fonts.h3())
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(lbl_title)

        self.input = QLineEdit(current_name)
        self.input.setFixedHeight(44)
        self.input.setFont(Fonts.body())
        self.input.setPlaceholderText("Material name...")
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.BG_SECONDARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 8px;
                color: {Colors.TEXT_PRIMARY};
                padding: 0 12px;
            }}
            QLineEdit:focus {{ border-color: {Colors.AMBER}; }}
        """)
        layout.addWidget(self.input)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedSize(120, 44)
        btn_cancel.setFont(Fonts.body())
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
            QPushButton:pressed {{ background-color: {Colors.BG_TERTIARY}; }}
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("OK")
        btn_ok.setFixedSize(120, 44)
        btn_ok.setFont(Fonts.body())
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.AMBER};
                color: {Colors.WHITE};
                border: none;
                border-radius: 8px;
            }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """)
        btn_ok.clicked.connect(self.accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def get_name(self) -> str:
        return self.input.text().strip()


class MaterialEditRow(QFrame):
    """소재 설정 편집 행"""

    value_changed = Signal()

    def __init__(self, label: str, value: float, unit: str,
                 min_val: float, max_val: float, step: float = 1.0,
                 allow_decimal: bool = False, parent=None):
        super().__init__(parent)

        self._value = value
        self._unit = unit
        self._min = min_val
        self._max = max_val
        self._label = label
        self._allow_decimal = allow_decimal

        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        self.lbl_label = QLabel(label)
        self.lbl_label.setFont(Fonts.body_small())
        self.lbl_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent; border: none;")
        self.lbl_label.setFixedWidth(120)

        self.lbl_value = QLabel()
        self.lbl_value.setFont(Fonts.body_small())
        self.lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_value.setStyleSheet(f"color: {Colors.AMBER}; background: transparent; border: none; font-weight: 600;")
        self._update_display()

        layout.addWidget(self.lbl_label)
        layout.addWidget(self.lbl_value, 1)

    def _update_display(self):
        self.lbl_value.setText(f"{self._value:g} {self._unit}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            keypad = NumericKeypad(
                title=self._label,
                value=self._value,
                unit=self._unit,
                min_val=self._min,
                max_val=self._max,
                allow_decimal=self._allow_decimal,
                parent=self.window()
            )
            keypad.value_confirmed.connect(self._on_confirmed)
            keypad.exec()
        super().mousePressEvent(event)

    def _on_confirmed(self, value: float):
        self._value = value
        self._update_display()
        self.value_changed.emit()

    def get_value(self) -> float:
        return self._value

    def set_value(self, value: float):
        self._value = value
        self._update_display()


class MaterialEditPairRow(QFrame):
    """한 행에 2개의 설정값을 나란히 배치"""

    value_changed = Signal()

    def __init__(self, left: MaterialEditRow, right: MaterialEditRow = None, parent=None):
        super().__init__(parent)
        self._left = left
        self._right = right

        self.setFixedHeight(36)
        self.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        layout.addWidget(left, 1)
        if right:
            layout.addWidget(right, 1)

        left.value_changed.connect(self.value_changed.emit)
        if right:
            right.value_changed.connect(self.value_changed.emit)


class TestMaterialPage(BasePage):
    """테스트 모드 소재 프리셋 관리 페이지"""

    go_print_test = Signal()

    def __init__(self, parent=None):
        super().__init__("Test Material", show_back=True, parent=parent)
        self._current_material_name = ""
        self._setup_content()
        self._load_materials()

    def _setup_content(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)

        # === 좌측: 소재 리스트 ===
        left_frame = QFrame()
        left_frame.setFixedWidth(240)
        left_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        lbl_list_title = QLabel("Test Presets")
        lbl_list_title.setFont(Fonts.h3())
        lbl_list_title.setAlignment(Qt.AlignCenter)
        lbl_list_title.setStyleSheet(f"color: {Colors.AMBER}; background: transparent; border: none;")
        left_layout.addWidget(lbl_list_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QWidget {{ background: transparent; }}
        """)
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_widget)
        left_layout.addWidget(scroll, 1)

        # Add / Delete 버튼
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_add = QPushButton("Add")
        self.btn_add.setFixedHeight(36)
        self.btn_add.setFont(Fonts.body_small())
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.AMBER};
                color: {Colors.WHITE};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """)
        self.btn_add.clicked.connect(self._on_add)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setFixedHeight(36)
        self.btn_delete.setFont(Fonts.body_small())
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_PRIMARY};
                color: {Colors.RED};
                border: 1px solid {Colors.RED};
                border-radius: 6px;
            }}
            QPushButton:pressed {{ background-color: {Colors.RED}; color: {Colors.WHITE}; }}
        """)
        self.btn_delete.clicked.connect(self._on_delete)

        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_delete)
        left_layout.addLayout(btn_row)

        # === 우측: 편집 패널 ===
        right_frame = QFrame()
        right_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(8)

        # 소재 이름
        self.lbl_material_name = QPushButton("Select Material")
        self.lbl_material_name.setFixedHeight(40)
        self.lbl_material_name.setFont(Fonts.h3())
        self.lbl_material_name.setCursor(Qt.PointingHandCursor)
        self.lbl_material_name.setStyleSheet(f"""
            QPushButton {{
                color: {Colors.AMBER};
                background: transparent;
                border: none;
                border-bottom: 2px solid {Colors.AMBER};
            }}
            QPushButton:pressed {{ opacity: 0.7; }}
        """)
        self.lbl_material_name.clicked.connect(self._on_rename)
        right_layout.addWidget(self.lbl_material_name)

        right_layout.addSpacing(4)

        # 편집 행 (12필드, 2개씩 6줄)
        self.row_blade_speed = MaterialEditRow("Blade Spd 1", 5, "mm/s", 1, 100)
        self.row_blade_speed2 = MaterialEditRow("Blade Spd 2", 20, "mm/s", 1, 100)
        self.row_blade_boundary = MaterialEditRow("Boundary", 60.0, "mm", 0, 140, allow_decimal=True)
        self.row_led_power = MaterialEditRow("LED Power", 43, "%", 9, 100)
        self.row_y_dispense = MaterialEditRow("Resin Dist.", 1.0, "mm", 0.1, 10.0, allow_decimal=True)
        self.row_y_speed = MaterialEditRow("Resin Speed", 3, "mm/s", 1, 15)
        self.row_y_delay = MaterialEditRow("Resin Delay", 5.0, "s", 0.0, 300.0, allow_decimal=True)
        self.row_y_pull_dist = MaterialEditRow("Pull Dist.", 0.0, "mm", 0.0, 10.0, allow_decimal=True)
        self.row_y_pull_delay = MaterialEditRow("Pull Delay", 2.0, "s", 0.0, 20.0, allow_decimal=True)
        self.row_y_return_dist = MaterialEditRow("Return Dist.", 0.0, "mm", 0.0, 10.0, allow_decimal=True)
        self.row_y_return_delay = MaterialEditRow("Return Delay", 2.0, "s", 0.0, 20.0, allow_decimal=True)
        self.row_blade_start = MaterialEditRow("Blade Start", 0.0, "mm", 0.0, 20.0, allow_decimal=True)
        self.row_blade_end = MaterialEditRow("Blade End", 130.0, "mm", 120.0, 140.0, allow_decimal=True)
        self.row_led_delay = MaterialEditRow("LED Delay", 5.0, "s", 1.0, 60.0, allow_decimal=True)

        # Leveling ON/OFF 토글 버튼
        self._leveling_on = True
        self.btn_leveling = QPushButton("Leveling ON")
        self.btn_leveling.setFixedHeight(36)
        self.btn_leveling.setFont(Fonts.body_small())
        self.btn_leveling.setCursor(Qt.PointingHandCursor)
        self.btn_leveling.clicked.connect(self._on_leveling_toggle)
        self._update_leveling_style()

        # Resin Delay + Leveling 토글 행
        self._leveling_row = QFrame()
        self._leveling_row.setFixedHeight(36)
        self._leveling_row.setStyleSheet("background: transparent; border: none;")
        lev_layout = QHBoxLayout(self._leveling_row)
        lev_layout.setContentsMargins(0, 0, 0, 0)
        lev_layout.setSpacing(6)
        lev_layout.addWidget(self.row_y_delay, 1)
        lev_layout.addWidget(self.btn_leveling, 1)

        self._pair_rows = [
            MaterialEditPairRow(self.row_blade_speed, self.row_blade_speed2),
            MaterialEditPairRow(self.row_blade_boundary, self.row_led_power),
            MaterialEditPairRow(self.row_y_dispense, self.row_y_speed),
            MaterialEditPairRow(self.row_y_pull_dist, self.row_y_pull_delay),
            MaterialEditPairRow(self.row_y_return_dist, self.row_y_return_delay),
            MaterialEditPairRow(self.row_blade_start, self.row_blade_end),
            MaterialEditPairRow(self.row_led_delay),
        ]

        for pair in self._pair_rows:
            pair.value_changed.connect(self._on_value_changed)
            right_layout.addWidget(pair)
            if pair is self._pair_rows[2]:  # Resin Dist/Speed 다음에 Resin Delay + Leveling 행 삽입
                self.row_y_delay.value_changed.connect(self._on_value_changed)
                right_layout.addWidget(self._leveling_row)

        right_layout.addStretch()

        # Print Test 버튼
        self.btn_print_test = QPushButton("Print Test")
        self.btn_print_test.setFixedHeight(50)
        self.btn_print_test.setFont(Fonts.h3())
        self.btn_print_test.setCursor(Qt.PointingHandCursor)
        self.btn_print_test.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.NAVY};
                border: none;
                border-radius: {Radius.LG}px;
                color: {Colors.WHITE};
                font-weight: bold;
            }}
            QPushButton:pressed {{ background-color: {Colors.NAVY_LIGHT}; }}
        """)
        self.btn_print_test.clicked.connect(self.go_print_test.emit)
        right_layout.addWidget(self.btn_print_test)

        main_layout.addWidget(left_frame)
        main_layout.addWidget(right_frame, 1)
        self.content_layout.addLayout(main_layout)

    def _load_materials(self):
        settings = get_settings()
        materials = settings.get_test_materials()

        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for mat in materials:
            btn = QPushButton(mat.name)
            btn.setFixedHeight(40)
            btn.setFont(Fonts.body())
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, name=mat.name: self._select_material(name))
            self._list_layout.insertWidget(self._list_layout.count() - 1, btn)

        selected = settings.get_selected_test_material()
        if selected:
            self._select_material(selected)
        elif materials:
            self._select_material(materials[0].name)

        self._update_list_styles()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_materials()

    def _update_list_styles(self):
        for i in range(self._list_layout.count()):
            item = self._list_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QPushButton):
                btn = item.widget()
                if btn.text() == self._current_material_name:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {Colors.AMBER};
                            color: {Colors.WHITE};
                            border: none;
                            border-radius: 8px;
                            font-weight: 600;
                        }}
                    """)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {Colors.BG_PRIMARY};
                            color: {Colors.TEXT_PRIMARY};
                            border: 1px solid {Colors.BORDER};
                            border-radius: 8px;
                        }}
                        QPushButton:pressed {{ background-color: {Colors.BG_TERTIARY}; }}
                    """)

    def _select_material(self, name: str):
        settings = get_settings()
        preset = settings.get_test_material_by_name(name)
        if not preset:
            return

        self._current_material_name = name
        settings.set_selected_test_material(name)

        self.lbl_material_name.setText(name)
        self.row_blade_speed.set_value(preset.blade_speed)
        self.row_blade_speed2.set_value(preset.blade_speed2)
        self.row_blade_boundary.set_value(preset.blade_boundary)
        self.row_led_power.set_value(preset.led_power)
        self.row_y_dispense.set_value(preset.y_dispense_distance)
        self.row_y_speed.set_value(preset.y_dispense_speed)
        self.row_y_delay.set_value(preset.y_dispense_delay)
        self.row_y_pull_dist.set_value(preset.y_pull_distance)
        self.row_y_pull_delay.set_value(preset.y_pull_delay)
        self.row_y_return_dist.set_value(preset.y_return_distance)
        self.row_y_return_delay.set_value(preset.y_return_delay)
        self.row_blade_start.set_value(preset.blade_start)
        self.row_blade_end.set_value(preset.blade_end)
        self.row_led_delay.set_value(preset.led_delay)
        self._leveling_on = preset.initial_leveling
        self._update_leveling_style()

        self._update_list_styles()

    def _on_value_changed(self):
        if not self._current_material_name:
            return

        preset = TestMaterialPreset(
            name=self._current_material_name,
            blade_speed=int(self.row_blade_speed.get_value()),
            blade_speed2=int(self.row_blade_speed2.get_value()),
            blade_boundary=self.row_blade_boundary.get_value(),
            led_power=int(self.row_led_power.get_value()),
            y_dispense_distance=self.row_y_dispense.get_value(),
            y_dispense_speed=int(self.row_y_speed.get_value()),
            y_dispense_delay=self.row_y_delay.get_value(),
            y_pull_distance=self.row_y_pull_dist.get_value(),
            y_pull_delay=self.row_y_pull_delay.get_value(),
            y_return_distance=self.row_y_return_dist.get_value(),
            y_return_delay=self.row_y_return_delay.get_value(),
            blade_start=self.row_blade_start.get_value(),
            blade_end=self.row_blade_end.get_value(),
            led_delay=self.row_led_delay.get_value(),
            initial_leveling=self._leveling_on,
        )
        get_settings().update_test_material(self._current_material_name, preset)

    def _on_leveling_toggle(self):
        """초기 평탄화 ON/OFF 토글"""
        self._leveling_on = not self._leveling_on
        self._update_leveling_style()
        self._on_value_changed()

    def _update_leveling_style(self):
        """토글 버튼 스타일 갱신"""
        if self._leveling_on:
            self.btn_leveling.setText("Leveling ON")
            self.btn_leveling.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.AMBER};
                    color: {Colors.WHITE};
                    border: none;
                    border-radius: 6px;
                    font-weight: 600;
                }}
                QPushButton:pressed {{ background-color: #D97706; }}
            """)
        else:
            self.btn_leveling.setText("Leveling OFF")
            self.btn_leveling.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_PRIMARY};
                    color: {Colors.TEXT_SECONDARY};
                    border: 1px solid {Colors.BORDER};
                    border-radius: 6px;
                }}
                QPushButton:pressed {{ background-color: {Colors.BG_TERTIARY}; }}
            """)

    def _on_add(self):
        dialog = TestMaterialNameDialog("New Test Material", "", self)
        if dialog.exec() == QDialog.Accepted:
            name = dialog.get_name()
            if name:
                get_settings().add_test_material(TestMaterialPreset(name=name))
                self._load_materials()
                self._select_material(name)

    def _on_delete(self):
        if not self._current_material_name:
            return
        if get_settings().delete_test_material(self._current_material_name):
            self._current_material_name = ""
            self._load_materials()

    def _on_rename(self):
        if not self._current_material_name:
            return
        dialog = TestMaterialNameDialog("Rename", self._current_material_name, self)
        if dialog.exec() == QDialog.Accepted:
            new_name = dialog.get_name()
            if new_name and new_name != self._current_material_name:
                settings = get_settings()
                preset = settings.get_test_material_by_name(self._current_material_name)
                if preset:
                    old_name = self._current_material_name
                    preset.name = new_name
                    settings.update_test_material(old_name, preset)
                    self._current_material_name = new_name
                    self._load_materials()
