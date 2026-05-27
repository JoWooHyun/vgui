"""
VERICOM DLP 3D Printer GUI - Print Test Page
테스트 모드 설정 요약 + 레이어 설정/시작 + 진행 상태 (통합 페이지)
좌측: 설정 요약 (항상 표시), 우측: 대기 모드 ↔ 진행 모드 전환
"""

import time as _time

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QWidget, QLabel, QPushButton
)
from PySide6.QtCore import Signal, Qt, QTimer

from pages.base_page import BasePage
from components.numeric_keypad import NumericKeypad
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius
from controllers.settings_manager import get_settings


class PrintTestPage(BasePage):
    """테스트 프린트 통합 페이지 (설정 + 진행)"""

    # 대기 모드 시그널
    start_test = Signal(dict)

    # 진행 모드 시그널
    go_home = Signal()
    pause_requested = Signal()
    resume_requested = Signal()
    stop_requested = Signal()
    refill_completed = Signal()
    manual_feed_selected = Signal()

    def __init__(self, parent=None):
        super().__init__("Print Test", show_back=True, parent=parent)
        self.settings = get_settings()
        self._total_layers = 10
        self._layer_height = 0.05
        self._z_offset = 0.0
        self._settle_time = 0.0
        self._is_paused = False
        self._start_time = 0
        self._is_running = False
        self._setup_content()

        # 경과 시간 타이머
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_elapsed)
        self._timer.setInterval(1000)

    def _setup_content(self):
        self.content_layout.setContentsMargins(20, 10, 20, 10)

        main_row = QHBoxLayout()
        main_row.setSpacing(20)

        # === 좌측: 설정 요약 (항상 표시) ===
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
            ("Z Offset", "z_offset", "mm"),
            ("Settle Time", "settle_time", "s"),
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

        # === 우측 패널 ===
        right_panel = QWidget()
        right_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.BG_SECONDARY};
                border-radius: {Radius.LG}px;
            }}
        """)
        self._right_layout = QVBoxLayout(right_panel)
        self._right_layout.setContentsMargins(20, 15, 20, 15)
        self._right_layout.setSpacing(12)

        # --- 대기 모드 위젯들 ---
        self._setup_widgets = []

        # 레이어 수
        row_layers = QHBoxLayout()
        lbl_layers = QLabel("Layers:")
        lbl_layers.setFont(Fonts.h3())
        lbl_layers.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        row_layers.addWidget(lbl_layers)
        self._setup_widgets.append(lbl_layers)

        self.lbl_layer_count = QLabel(str(self._total_layers))
        self.lbl_layer_count.setFont(Fonts.h2())
        self.lbl_layer_count.setAlignment(Qt.AlignCenter)
        self.lbl_layer_count.setStyleSheet(f"color: {Colors.AMBER}; background: transparent; font-weight: bold;")
        self.lbl_layer_count.mousePressEvent = lambda e: self._edit_value("layers")
        row_layers.addWidget(self.lbl_layer_count)
        self._setup_widgets.append(self.lbl_layer_count)
        self._right_layout.addLayout(row_layers)

        # 레이어 높이
        row_height = QHBoxLayout()
        lbl_h = QLabel("Layer Height:")
        lbl_h.setFont(Fonts.h3())
        lbl_h.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        row_height.addWidget(lbl_h)
        self._setup_widgets.append(lbl_h)

        self.lbl_layer_height = QLabel(f"{self._layer_height} mm")
        self.lbl_layer_height.setFont(Fonts.h2())
        self.lbl_layer_height.setAlignment(Qt.AlignCenter)
        self.lbl_layer_height.setStyleSheet(f"color: {Colors.AMBER}; background: transparent; font-weight: bold;")
        self.lbl_layer_height.mousePressEvent = lambda e: self._edit_value("height")
        row_height.addWidget(self.lbl_layer_height)
        self._setup_widgets.append(self.lbl_layer_height)
        self._right_layout.addLayout(row_height)

        # Z 오프셋
        row_zoffset = QHBoxLayout()
        lbl_zo = QLabel("Z Offset:")
        lbl_zo.setFont(Fonts.h3())
        lbl_zo.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        row_zoffset.addWidget(lbl_zo)
        self._setup_widgets.append(lbl_zo)

        self.lbl_z_offset = QLabel(f"{self._z_offset:.2f} mm")
        self.lbl_z_offset.setFont(Fonts.h2())
        self.lbl_z_offset.setAlignment(Qt.AlignCenter)
        self.lbl_z_offset.setStyleSheet(f"color: {Colors.AMBER}; background: transparent; font-weight: bold;")
        self.lbl_z_offset.mousePressEvent = lambda e: self._edit_value("z_offset")
        row_zoffset.addWidget(self.lbl_z_offset)
        self._setup_widgets.append(self.lbl_z_offset)
        self._right_layout.addLayout(row_zoffset)

        # Settle Time
        row_settle = QHBoxLayout()
        lbl_st = QLabel("Settle Time:")
        lbl_st.setFont(Fonts.h3())
        lbl_st.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        row_settle.addWidget(lbl_st)
        self._setup_widgets.append(lbl_st)

        self.lbl_settle_time = QLabel(f"{self._settle_time:.1f} s")
        self.lbl_settle_time.setFont(Fonts.h2())
        self.lbl_settle_time.setAlignment(Qt.AlignCenter)
        self.lbl_settle_time.setStyleSheet(f"color: {Colors.AMBER}; background: transparent; font-weight: bold;")
        self.lbl_settle_time.mousePressEvent = lambda e: self._edit_value("settle_time")
        row_settle.addWidget(self.lbl_settle_time)
        self._setup_widgets.append(self.lbl_settle_time)
        self._right_layout.addLayout(row_settle)

        # START 버튼
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
        self._setup_widgets.append(self.btn_start)

        # stretch + START
        self._setup_stretch = self._right_layout.addStretch()
        self._right_layout.addWidget(self.btn_start)

        # --- 진행 모드 위젯들 (처음에 숨김) ---
        self._progress_widgets = []

        # 상태 라벨
        self.lbl_status = QLabel("Initializing...")
        self.lbl_status.setFont(Fonts.h2())
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet(f"color: {Colors.AMBER}; font-weight: bold;")
        self._right_layout.addWidget(self.lbl_status)
        self._progress_widgets.append(self.lbl_status)

        # 레이어 진행
        self.lbl_progress = QLabel("Layer: 0 / 0")
        self.lbl_progress.setFont(Fonts.h1())
        self.lbl_progress.setAlignment(Qt.AlignCenter)
        self.lbl_progress.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: bold;")
        self._right_layout.addWidget(self.lbl_progress)
        self._progress_widgets.append(self.lbl_progress)

        # 시간 정보
        time_row = QHBoxLayout()
        time_row.setSpacing(30)

        elapsed_col = QVBoxLayout()
        self._lbl_elapsed_title = QLabel("Elapsed")
        self._lbl_elapsed_title.setFont(Fonts.caption())
        self._lbl_elapsed_title.setAlignment(Qt.AlignCenter)
        self._lbl_elapsed_title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        elapsed_col.addWidget(self._lbl_elapsed_title)
        self._progress_widgets.append(self._lbl_elapsed_title)

        self.lbl_elapsed = QLabel("00:00:00")
        self.lbl_elapsed.setFont(Fonts.h3())
        self.lbl_elapsed.setAlignment(Qt.AlignCenter)
        self.lbl_elapsed.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        elapsed_col.addWidget(self.lbl_elapsed)
        self._progress_widgets.append(self.lbl_elapsed)
        time_row.addLayout(elapsed_col)

        remain_col = QVBoxLayout()
        self._lbl_remain_title = QLabel("Remaining")
        self._lbl_remain_title.setFont(Fonts.caption())
        self._lbl_remain_title.setAlignment(Qt.AlignCenter)
        self._lbl_remain_title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        remain_col.addWidget(self._lbl_remain_title)
        self._progress_widgets.append(self._lbl_remain_title)

        self.lbl_remaining = QLabel("--:--:--")
        self.lbl_remaining.setFont(Fonts.h3())
        self.lbl_remaining.setAlignment(Qt.AlignCenter)
        self.lbl_remaining.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        remain_col.addWidget(self.lbl_remaining)
        self._progress_widgets.append(self.lbl_remaining)
        time_row.addLayout(remain_col)

        self._time_widget = QWidget()
        self._time_widget.setLayout(time_row)
        self._time_widget.setStyleSheet("background: transparent; border: none;")
        self._right_layout.addWidget(self._time_widget)
        self._progress_widgets.append(self._time_widget)

        self._progress_stretch = self._right_layout.addStretch()

        # 진행 모드 버튼들
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_pause = QPushButton("PAUSE")
        self.btn_pause.setFixedSize(160, 50)
        self.btn_pause.setFont(Fonts.h3())
        self.btn_pause.setCursor(Qt.PointingHandCursor)
        self.btn_pause.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.AMBER};
                border: none; border-radius: {Radius.LG}px;
                color: {Colors.WHITE}; font-weight: bold;
            }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """)
        self.btn_pause.clicked.connect(self._on_pause_resume)
        btn_row.addWidget(self.btn_pause)
        self._progress_widgets.append(self.btn_pause)

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setFixedSize(160, 50)
        self.btn_stop.setFont(Fonts.h3())
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.RED};
                border: none; border-radius: {Radius.LG}px;
                color: {Colors.WHITE}; font-weight: bold;
            }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """)
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        btn_row.addWidget(self.btn_stop)
        self._progress_widgets.append(self.btn_stop)

        self.btn_home = QPushButton("HOME")
        self.btn_home.setFixedSize(160, 50)
        self.btn_home.setFont(Fonts.h3())
        self.btn_home.setCursor(Qt.PointingHandCursor)
        self.btn_home.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.NAVY};
                border: none; border-radius: {Radius.LG}px;
                color: {Colors.WHITE}; font-weight: bold;
            }}
            QPushButton:pressed {{ background-color: {Colors.NAVY_LIGHT}; }}
        """)
        self.btn_home.clicked.connect(self._on_home)
        btn_row.addWidget(self.btn_home)
        self._progress_widgets.append(self.btn_home)

        self._btn_row_widget = QWidget()
        self._btn_row_widget.setLayout(btn_row)
        self._btn_row_widget.setStyleSheet("background: transparent; border: none;")
        self._right_layout.addWidget(self._btn_row_widget)
        self._progress_widgets.append(self._btn_row_widget)

        # Resin empty 버튼 행
        resin_row = QHBoxLayout()
        resin_row.setSpacing(12)

        self.btn_refill = QPushButton("REFILL DONE")
        self.btn_refill.setFixedSize(160, 50)
        self.btn_refill.setFont(Fonts.h3())
        self.btn_refill.setCursor(Qt.PointingHandCursor)
        self.btn_refill.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.GREEN};
                border: none; border-radius: {Radius.LG}px;
                color: {Colors.WHITE}; font-weight: bold;
            }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """)
        self.btn_refill.clicked.connect(self._on_refill_done)
        resin_row.addWidget(self.btn_refill)

        self.btn_manual_feed = QPushButton("MANUAL FEED")
        self.btn_manual_feed.setFixedSize(160, 50)
        self.btn_manual_feed.setFont(Fonts.h3())
        self.btn_manual_feed.setCursor(Qt.PointingHandCursor)
        self.btn_manual_feed.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.CYAN};
                border: none; border-radius: {Radius.LG}px;
                color: {Colors.WHITE}; font-weight: bold;
            }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """)
        self.btn_manual_feed.clicked.connect(self._on_manual_feed)
        resin_row.addWidget(self.btn_manual_feed)

        self._resin_row_widget = QWidget()
        self._resin_row_widget.setLayout(resin_row)
        self._resin_row_widget.setStyleSheet("background: transparent; border: none;")
        self._right_layout.addWidget(self._resin_row_widget)
        self._progress_widgets.append(self._resin_row_widget)

        main_row.addWidget(right_panel, 2)
        self.content_layout.addLayout(main_row)

        # 초기 상태: 대기 모드
        self._show_setup_mode()

    # ==================== 모드 전환 ====================

    def _show_setup_mode(self):
        """대기 모드 (설정 입력 + START)"""
        self._is_running = False
        # Back 버튼 활성화
        if hasattr(self, 'btn_back'):
            self.btn_back.show()

        for w in self._setup_widgets:
            w.show()
        for w in self._progress_widgets:
            w.hide()

    def _show_progress_mode(self):
        """진행 모드 (상태 + 버튼)"""
        self._is_running = True
        # 진행 중 Back 비활성화
        if hasattr(self, 'btn_back'):
            self.btn_back.hide()

        for w in self._setup_widgets:
            w.hide()
        for w in self._progress_widgets:
            w.show()

        # 초기 버튼 상태
        self.btn_pause.show()
        self.btn_pause.setText("PAUSE")
        self.btn_stop.show()
        self.btn_home.hide()
        self._resin_row_widget.hide()

    # ==================== 대기 모드 (기존 기능) ====================

    def showEvent(self, event):
        super().showEvent(event)
        if not self._is_running:
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

        self._labels["z_offset"].setText(f"{self._z_offset:.2f}")
        self._labels["settle_time"].setText(f"{self._settle_time:.1f}")

    def _edit_value(self, which: str):
        if self._is_running:
            return
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
        elif which == "z_offset":
            keypad = NumericKeypad(
                title="Z Offset (mm)",
                value=self._z_offset,
                min_val=0.0, max_val=1.0,
                allow_decimal=True,
                parent=self
            )
            if keypad.exec():
                self._z_offset = keypad.get_value()
                self.lbl_z_offset.setText(f"{self._z_offset:.2f} mm")
        elif which == "settle_time":
            keypad = NumericKeypad(
                title="Settle Time (s)",
                value=self._settle_time,
                min_val=0.0, max_val=30.0,
                allow_decimal=True,
                parent=self
            )
            if keypad.exec():
                self._settle_time = keypad.get_value()
                self.lbl_settle_time.setText(f"{self._settle_time:.1f} s")

    def _on_start(self):
        preset = self.settings.get_selected_test_material_preset()

        params = {
            'totalLayer': self._total_layers,
            'layerHeight': self._layer_height,
            'zOffset': self._z_offset,
            'settleTime': self._settle_time,
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

    # ==================== 진행 모드 (TestProgressPage에서 이식) ====================

    def start_progress(self, total_layers: int):
        """테스트 시작 — 진행 모드 전환"""
        self._show_progress_mode()
        self._total_layers_progress = total_layers
        self._current_layer = 0
        self._start_time = _time.monotonic()
        self._is_paused = False

        self.lbl_status.setText("Testing...")
        self.lbl_status.setStyleSheet(f"color: {Colors.AMBER}; font-weight: bold;")
        self.lbl_progress.setText(f"Layer: 0 / {total_layers}")
        self.lbl_elapsed.setText("00:00:00")
        self.lbl_remaining.setText("--:--:--")

        self._timer.start()

    def update_progress(self, current: int, total: int):
        self._current_layer = current
        self._total_layers_progress = total
        self.lbl_progress.setText(f"Layer: {current} / {total}")

        if current > 0:
            elapsed = _time.monotonic() - self._start_time
            per_layer = elapsed / current
            remaining = per_layer * (total - current)
            self.lbl_remaining.setText(self._format_time(remaining))

    def show_completed(self):
        self._timer.stop()
        self.lbl_status.setText("TEST COMPLETED")
        self.lbl_status.setStyleSheet(f"color: {Colors.GREEN}; font-weight: bold;")
        self.btn_pause.hide()
        self.btn_stop.hide()
        self.btn_home.show()
        self._resin_row_widget.hide()

    def show_stopped(self):
        self._timer.stop()
        self.lbl_status.setText("TEST STOPPED")
        self.lbl_status.setStyleSheet(f"color: {Colors.RED}; font-weight: bold;")
        self.btn_pause.hide()
        self.btn_stop.hide()
        self.btn_home.show()
        self._resin_row_widget.hide()

    def show_error(self, message: str):
        self._timer.stop()
        self.lbl_status.setText(f"ERROR: {message}")
        self.lbl_status.setStyleSheet(f"color: {Colors.RED}; font-weight: bold;")
        self.btn_pause.hide()
        self.btn_stop.hide()
        self.btn_home.show()
        self._resin_row_widget.hide()

    def show_resin_empty(self):
        self.lbl_status.setText("RESIN EMPTY")
        self.lbl_status.setStyleSheet(f"color: {Colors.AMBER}; font-weight: bold;")
        self.btn_pause.hide()
        self.btn_stop.show()
        self._resin_row_widget.show()

    def _on_refill_done(self):
        self._resin_row_widget.hide()
        self.btn_pause.show()
        self.btn_pause.setText("PAUSE")
        self._is_paused = False
        self.lbl_status.setText("Testing...")
        self.lbl_status.setStyleSheet(f"color: {Colors.AMBER}; font-weight: bold;")
        self.refill_completed.emit()

    def _on_manual_feed(self):
        self._resin_row_widget.hide()
        self.btn_pause.show()
        self.btn_pause.setText("PAUSE")
        self._is_paused = False
        self.lbl_status.setText("Testing (Manual)...")
        self.lbl_status.setStyleSheet(f"color: {Colors.AMBER}; font-weight: bold;")
        self.manual_feed_selected.emit()

    def _on_pause_resume(self):
        if self._is_paused:
            self._is_paused = False
            self.btn_pause.setText("PAUSE")
            self.lbl_status.setText("Testing...")
            self.lbl_status.setStyleSheet(f"color: {Colors.AMBER}; font-weight: bold;")
            self.resume_requested.emit()
        else:
            self._is_paused = True
            self.btn_pause.setText("RESUME")
            self.lbl_status.setText("PAUSED")
            self.lbl_status.setStyleSheet(f"color: {Colors.AMBER}; font-weight: bold;")
            self.pause_requested.emit()

    def _on_home(self):
        """HOME 클릭 — 대기 모드로 복원 후 메인으로"""
        self._timer.stop()
        self._show_setup_mode()
        self.go_home.emit()

    def _update_elapsed(self):
        elapsed = _time.monotonic() - self._start_time
        self.lbl_elapsed.setText(self._format_time(elapsed))

    @staticmethod
    def _format_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
