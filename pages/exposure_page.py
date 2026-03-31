"""
VERICOM DLP 3D Printer GUI - Exposure Page
NVR2+ 테스트 패턴 노출 + 트레이 클리닝 통합
"""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt, QTimer, QSize

from pages.base_page import BasePage
from components.number_dial import NumberDial
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius
from styles.icons import Icons


# 패턴 정의
PATTERNS = [
    {
        "key": "ramp",
        "label": "Gradient",
        "icon": Icons.PATTERN_RAMP,
        "desc": "밝기 그라데이션 패턴을 노출합니다",
        "max_time": 60,
    },
    {
        "key": "checker",
        "label": "Checker",
        "icon": Icons.PATTERN_CHECKER,
        "desc": "체크무늬 패턴을 노출합니다",
        "max_time": 60,
    },
    {
        "key": "logo",
        "label": "Logo",
        "icon": Icons.PATTERN_LOGO,
        "desc": "로고 패턴을 노출합니다",
        "max_time": 60,
    },
    {
        "key": "test_image",
        "label": "20x20",
        "icon": Icons.CALIBRATION,
        "desc": "20x20mm 사각형을 노출하여 투영 크기를 검증합니다",
        "max_time": 60,
    },
    {
        "key": "clean",
        "label": "Clean",
        "icon": Icons.SQUARE_HALF,
        "desc": "전체 화면을 노출하여 트레이 바닥을 경화시킵니다",
        "max_time": 120,
    },
]


class PatternButton(QPushButton):
    """패턴 선택 버튼 (아이콘 + 텍스트)"""

    def __init__(self, icon_svg: str, label: str, parent=None):
        super().__init__(parent)

        self._selected = False
        self._icon_svg = icon_svg
        self._label = label
        self.setFixedSize(100, 100)
        self.setCursor(Qt.PointingHandCursor)

        # 내부 레이아웃
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 8)
        layout.setSpacing(4)

        layout.addStretch()

        # 아이콘
        self._icon_label = QLabel()
        self._icon_label.setAlignment(Qt.AlignCenter)
        self._icon_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._icon_label, alignment=Qt.AlignCenter)

        # 텍스트
        self._text_label = QLabel(label)
        self._text_label.setAlignment(Qt.AlignCenter)
        self._text_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._text_label, alignment=Qt.AlignCenter)

        layout.addStretch()

        self._update_style()

    def _update_style(self):
        """선택 상태에 따른 스타일 업데이트"""
        icon_size = 40
        if self._selected:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.CYAN};
                    border: 2px solid {Colors.CYAN};
                    border-radius: {Radius.MD}px;
                }}
                QPushButton:pressed {{
                    background-color: {Colors.CYAN_LIGHT};
                }}
            """)
            pixmap = Icons.get_pixmap(self._icon_svg, icon_size, Colors.WHITE)
            self._text_label.setStyleSheet(f"""
                color: {Colors.WHITE};
                font-size: 12px; font-weight: 600;
                background: transparent; border: none;
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_SECONDARY};
                    border: 2px solid {Colors.CYAN};
                    border-radius: {Radius.MD}px;
                }}
                QPushButton:pressed {{
                    background-color: {Colors.BG_TERTIARY};
                }}
            """)
            pixmap = Icons.get_pixmap(self._icon_svg, icon_size, Colors.CYAN)
            self._text_label.setStyleSheet(f"""
                color: {Colors.CYAN};
                font-size: 12px; font-weight: 600;
                background: transparent; border: none;
            """)

        self._icon_label.setPixmap(pixmap)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_style()

    def is_selected(self) -> bool:
        return self._selected


class ExposurePage(BasePage):
    """노출 테스트 페이지 (Exposure + Clean 통합)"""

    # 노출 시작/정지 시그널
    exposure_start = Signal(str, float)  # pattern_key, time
    exposure_stop = Signal()

    def __init__(self, parent=None):
        super().__init__("Exposure", show_back=True, parent=parent)

        self._current_pattern_idx = 1  # 기본: checker
        self._exposure_time = 5
        self._is_running = False

        # 타이머 (자동 정지용)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timer_done)

        self._setup_content()

    def _setup_content(self):
        """콘텐츠 구성"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 10, 40, 20)

        main_layout.addStretch(1)

        # === Row 1: 패턴 선택 버튼 5개 ===
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        self._pattern_buttons = []
        row1.addStretch()
        for i, p in enumerate(PATTERNS):
            btn = PatternButton(p["icon"], p["label"])
            btn.clicked.connect(lambda checked, idx=i: self._select_pattern(idx))
            self._pattern_buttons.append(btn)
            row1.addWidget(btn)
        row1.addStretch()

        # 기본 선택
        self._pattern_buttons[self._current_pattern_idx].set_selected(True)

        main_layout.addLayout(row1)

        # === Row 2: 설명 텍스트 ===
        self.lbl_desc = QLabel(PATTERNS[self._current_pattern_idx]["desc"])
        self.lbl_desc.setAlignment(Qt.AlignCenter)
        self.lbl_desc.setFont(Fonts.body())
        self.lbl_desc.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            background: transparent; border: none;
        """)
        main_layout.addWidget(self.lbl_desc)

        # === Row 3: 노출 시간 설정 ===
        row3 = QHBoxLayout()
        row3.setSpacing(20)

        self.btn_time = QPushButton(f"{self._exposure_time} sec")
        self.btn_time.setFixedSize(140, 50)
        self.btn_time.setCursor(Qt.PointingHandCursor)
        self.btn_time.setFont(Fonts.h2())
        self.btn_time.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                border: 2px solid {Colors.CYAN};
                border-radius: {Radius.MD}px;
                color: {Colors.NAVY};
            }}
            QPushButton:pressed {{
                background-color: {Colors.BG_TERTIARY};
            }}
        """)
        self.btn_time.clicked.connect(self._show_time_dial)

        row3.addStretch()
        row3.addWidget(self.btn_time)
        row3.addStretch()

        main_layout.addLayout(row3)

        main_layout.addStretch(2)

        # === Row 4: START/STOP 버튼 ===
        row4 = QHBoxLayout()

        self.btn_start = QPushButton("START")
        self.btn_start.setFixedSize(200, 60)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setFont(Fonts.h2())
        self.btn_start.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.NAVY};
                border: none;
                border-radius: {Radius.LG}px;
                color: {Colors.WHITE};
            }}
            QPushButton:pressed {{
                background-color: {Colors.NAVY_LIGHT};
            }}
        """)
        self.btn_start.clicked.connect(self._on_start)

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setFixedSize(200, 60)
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setFont(Fonts.h2())
        self.btn_stop.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.RED};
                border: none;
                border-radius: {Radius.LG}px;
                color: {Colors.WHITE};
            }}
            QPushButton:pressed {{
                background-color: {Colors.RED_LIGHT};
            }}
        """)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_stop.hide()

        row4.addStretch()
        row4.addWidget(self.btn_start)
        row4.addWidget(self.btn_stop)
        row4.addStretch()

        main_layout.addLayout(row4)

        self.content_layout.addLayout(main_layout)

    def _select_pattern(self, idx: int):
        """패턴 선택"""
        self._current_pattern_idx = idx

        # 버튼 선택 상태 업데이트
        for i, btn in enumerate(self._pattern_buttons):
            btn.set_selected(i == idx)

        # 설명 텍스트 업데이트
        self.lbl_desc.setText(PATTERNS[idx]["desc"])

    def _show_time_dial(self):
        """시간 설정 다이얼 표시"""
        if self._is_running:
            return

        pattern = PATTERNS[self._current_pattern_idx]

        dial = NumberDial(
            title="Exposure Time",
            initial_value=self._exposure_time,
            unit="sec",
            min_value=1,
            max_value=pattern["max_time"],
            step=1,
            decimals=0,
            parent=self
        )

        if dial.exec():
            self._exposure_time = int(dial.get_value())
            self.btn_time.setText(f"{self._exposure_time} sec")

    def _on_start(self):
        """노출 시작"""
        self._is_running = True

        # UI 업데이트
        self.btn_start.hide()
        self.btn_stop.show()

        # 패턴 버튼 비활성화
        for btn in self._pattern_buttons:
            btn.setEnabled(False)
        self.btn_time.setEnabled(False)

        # 타이머 시작 (자동 정지)
        self._timer.start(int(self._exposure_time * 1000))

        # 시그널 발생
        pattern_key = PATTERNS[self._current_pattern_idx]["key"]
        self.exposure_start.emit(pattern_key, self._exposure_time)

    def _on_stop(self):
        """노출 정지"""
        self._timer.stop()
        self._is_running = False

        # UI 업데이트
        self.btn_stop.hide()
        self.btn_start.show()

        # 패턴 버튼 활성화
        for btn in self._pattern_buttons:
            btn.setEnabled(True)
        self.btn_time.setEnabled(True)

        # 시그널 발생
        self.exposure_stop.emit()

    def _on_timer_done(self):
        """타이머 완료 (자동 정지)"""
        self._on_stop()

    @property
    def current_pattern_key(self) -> str:
        """현재 패턴 키 반환"""
        return PATTERNS[self._current_pattern_idx]["key"]
