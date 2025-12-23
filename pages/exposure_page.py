"""
VERICOM DLP 3D Printer GUI - Exposure Page
NVR2+ 테스트 패턴 노출
"""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal, Qt, QTimer, QSize

from pages.base_page import BasePage
from components.number_dial import NumberDial
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius
from styles.icons import Icons


class PatternIconButton(QPushButton):
    """패턴 선택 아이콘 버튼"""

    def __init__(self, icon_svg: str, parent=None):
        super().__init__(parent)

        self._selected = False
        self._icon_svg = icon_svg
        self.setFixedSize(100, 100)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()

    def _update_style(self):
        """선택 상태에 따른 스타일 업데이트"""
        icon_size = 64
        if self._selected:
            # 선택됨: Cyan 배경
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
            self.setIcon(Icons.get_icon(self._icon_svg, icon_size, Colors.WHITE))
        else:
            # 미선택: 회색 배경 + Cyan 테두리
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
            self.setIcon(Icons.get_icon(self._icon_svg, icon_size, Colors.CYAN))
        self.setIconSize(QSize(icon_size, icon_size))

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_style()

    def is_selected(self) -> bool:
        return self._selected


class ExposurePage(BasePage):
    """노출 테스트 페이지"""
    
    # 노출 시작/정지 시그널
    exposure_start = Signal(str, float)  # pattern, time
    exposure_stop = Signal()
    
    def __init__(self, parent=None):
        super().__init__("Exposure", show_back=True, parent=parent)
        
        self._current_pattern = "checker"  # 기본: 체스판
        self._exposure_time = 5  # 초 단위 (정수)
        self._is_running = False
        
        # 타이머 (자동 정지용)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timer_done)
        
        self._setup_content()
    
    def _setup_content(self):
        """콘텐츠 구성"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 20, 40, 30)

        # 상단 여백
        main_layout.addStretch(1)

        # === Row 1: Pattern Buttons ===
        row1 = QHBoxLayout()
        row1.setSpacing(20)

        self.btn_ramp = PatternIconButton(Icons.PATTERN_RAMP)
        self.btn_ramp.clicked.connect(lambda: self._select_pattern("ramp"))

        self.btn_checker = PatternIconButton(Icons.PATTERN_CHECKER)
        self.btn_checker.set_selected(True)  # 기본 선택: Checker
        self.btn_checker.clicked.connect(lambda: self._select_pattern("checker"))

        self.btn_logo = PatternIconButton(Icons.PATTERN_LOGO)
        self.btn_logo.clicked.connect(lambda: self._select_pattern("logo"))

        row1.addStretch()
        row1.addWidget(self.btn_ramp)
        row1.addWidget(self.btn_checker)
        row1.addWidget(self.btn_logo)
        row1.addStretch()

        main_layout.addLayout(row1)

        # === Row 2: Exposure Time ===
        row2 = QHBoxLayout()
        row2.setSpacing(20)

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

        row2.addStretch()
        row2.addWidget(self.btn_time)
        row2.addStretch()

        main_layout.addLayout(row2)

        # 하단 여백
        main_layout.addStretch(2)

        # === Row 3: START/STOP 버튼 ===
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
    
    def _select_pattern(self, pattern: str):
        """패턴 선택"""
        self._current_pattern = pattern
        self.btn_ramp.set_selected(pattern == "ramp")
        self.btn_checker.set_selected(pattern == "checker")
        self.btn_logo.set_selected(pattern == "logo")
    
    def _show_time_dial(self):
        """시간 설정 다이얼 표시"""
        if self._is_running:
            return
        
        dial = NumberDial(
            title="Exposure Time",
            initial_value=self._exposure_time,
            unit="sec",
            min_value=1,
            max_value=60,
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

        # 타이머 시작 (자동 정지)
        self._timer.start(int(self._exposure_time * 1000))

        # 시그널 발생
        self.exposure_start.emit(self._current_pattern, self._exposure_time)
    
    def _on_stop(self):
        """노출 정지"""
        self._timer.stop()
        self._is_running = False
        
        # UI 업데이트
        self.btn_stop.hide()
        self.btn_start.show()
        
        # 시그널 발생
        self.exposure_stop.emit()
    
    def _on_timer_done(self):
        """타이머 완료 (자동 정지)"""
        self._on_stop()

    def get_pattern_value(self) -> int:
        """현재 패턴 설정값 반환 (NVR2+ 명령용)"""
        if self._current_pattern == "ramp":
            return 0x01
        elif self._current_pattern == "checker":
            return 0x07
        else:  # logo
            return 0x00  # 이미지 패턴
