"""
VERICOM DLP 3D Printer GUI - Exposure Test Page
NVR2+ 테스트 패턴 노출 테스트
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton
)
from PySide6.QtCore import Signal, Qt, QTimer

from pages.base_page import BasePage
from components.number_dial import NumberDial
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius


class PatternButton(QPushButton):
    """패턴 선택 버튼"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        
        self._selected = False
        self.setFixedSize(140, 70)
        self.setCursor(Qt.PointingHandCursor)
        self.setText(text)
        self._update_style()
    
    def _update_style(self):
        """선택 상태에 따른 스타일 업데이트"""
        if self._selected:
            # 선택됨: Cyan 배경
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.CYAN};
                    border: 2px solid {Colors.CYAN};
                    border-radius: {Radius.MD}px;
                    color: {Colors.WHITE};
                    font-size: 18px;
                    font-weight: 600;
                }}
                QPushButton:pressed {{
                    background-color: {Colors.CYAN_LIGHT};
                }}
            """)
        else:
            # 미선택: 회색 배경 + Cyan 테두리
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_SECONDARY};
                    border: 2px solid {Colors.CYAN};
                    border-radius: {Radius.MD}px;
                    color: {Colors.CYAN};
                    font-size: 18px;
                    font-weight: 600;
                }}
                QPushButton:pressed {{
                    background-color: {Colors.BG_TERTIARY};
                }}
            """)
    
    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_style()
    
    def is_selected(self) -> bool:
        return self._selected


class FlipButton(QPushButton):
    """반전 토글 버튼"""
    
    toggled_state = Signal(bool)
    
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        
        self._active = False
        self.setFixedSize(140, 70)
        self.setCursor(Qt.PointingHandCursor)
        self.setText(text)
        self.clicked.connect(self._on_clicked)
        self._update_style()
    
    def _on_clicked(self):
        self._active = not self._active
        self._update_style()
        self.toggled_state.emit(self._active)
    
    def _update_style(self):
        """활성 상태에 따른 스타일 업데이트"""
        if self._active:
            # 활성: Cyan 배경
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.CYAN};
                    border: 2px solid {Colors.CYAN};
                    border-radius: {Radius.MD}px;
                    color: {Colors.WHITE};
                    font-size: 18px;
                    font-weight: 600;
                }}
                QPushButton:pressed {{
                    background-color: {Colors.CYAN_LIGHT};
                }}
            """)
        else:
            # 비활성: 회색 배경
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_SECONDARY};
                    border: 2px solid {Colors.BORDER};
                    border-radius: {Radius.MD}px;
                    color: {Colors.TEXT_PRIMARY};
                    font-size: 18px;
                    font-weight: 600;
                }}
                QPushButton:pressed {{
                    background-color: {Colors.BG_TERTIARY};
                }}
            """)
    
    def is_active(self) -> bool:
        return self._active
    
    def set_active(self, active: bool):
        self._active = active
        self._update_style()


class ExposurePage(BasePage):
    """노출 테스트 페이지"""
    
    # 노출 시작/정지 시그널
    exposure_start = Signal(str, bool, bool, float)  # pattern, h_flip, v_flip, time
    exposure_stop = Signal()
    
    def __init__(self, parent=None):
        super().__init__("Exposure Test", show_back=True, parent=parent)
        
        self._current_pattern = "ramp"
        self._exposure_time = 5.0
        self._is_running = False
        
        # 타이머 (자동 정지용)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timer_done)
        
        self._setup_content()
    
    def _setup_content(self):
        """콘텐츠 구성"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(40, 20, 40, 30)
        
        # === Row 1: Test Pattern ===
        row1 = QHBoxLayout()
        row1.setSpacing(20)
        
        lbl_pattern = QLabel("Test Pattern")
        lbl_pattern.setFixedWidth(160)
        lbl_pattern.setFont(Fonts.body())
        lbl_pattern.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            background-color: {Colors.BG_PRIMARY};
            border: none;
        """)
        
        self.btn_ramp = PatternButton("Ramp")
        self.btn_ramp.set_selected(True)
        self.btn_ramp.clicked.connect(lambda: self._select_pattern("ramp"))
        
        self.btn_checker = PatternButton("Checker")
        self.btn_checker.clicked.connect(lambda: self._select_pattern("checker"))
        
        row1.addWidget(lbl_pattern)
        row1.addWidget(self.btn_ramp)
        row1.addWidget(self.btn_checker)
        row1.addStretch()
        
        main_layout.addLayout(row1)
        
        # === Row 2: Image Flip ===
        row2 = QHBoxLayout()
        row2.setSpacing(20)
        
        lbl_flip = QLabel("Image Flip")
        lbl_flip.setFixedWidth(160)
        lbl_flip.setFont(Fonts.body())
        lbl_flip.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            background-color: {Colors.BG_PRIMARY};
            border: none;
        """)
        
        self.btn_h_flip = FlipButton("H Flip")
        self.btn_v_flip = FlipButton("V Flip")
        
        row2.addWidget(lbl_flip)
        row2.addWidget(self.btn_h_flip)
        row2.addWidget(self.btn_v_flip)
        row2.addStretch()
        
        main_layout.addLayout(row2)
        
        # === Row 3: Exposure Time ===
        row3 = QHBoxLayout()
        row3.setSpacing(20)
        
        lbl_time = QLabel("Exposure Time")
        lbl_time.setFixedWidth(160)
        lbl_time.setFont(Fonts.body())
        lbl_time.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            background-color: {Colors.BG_PRIMARY};
            border: none;
        """)
        
        self.btn_time = QPushButton(f"{self._exposure_time:.1f} sec")
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
        
        row3.addWidget(lbl_time)
        row3.addWidget(self.btn_time)
        row3.addStretch()
        
        main_layout.addLayout(row3)
        
        # 빈 공간
        main_layout.addStretch()
        
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
    
    def _select_pattern(self, pattern: str):
        """패턴 선택"""
        self._current_pattern = pattern
        self.btn_ramp.set_selected(pattern == "ramp")
        self.btn_checker.set_selected(pattern == "checker")
    
    def _show_time_dial(self):
        """시간 설정 다이얼 표시"""
        if self._is_running:
            return
        
        dial = NumberDial(
            title="Exposure Time",
            initial_value=self._exposure_time,
            unit="sec",
            min_value=1.0,
            max_value=60.0,
            step=0.5,
            decimals=1,
            parent=self
        )
        
        if dial.exec():
            self._exposure_time = dial.get_value()
            self.btn_time.setText(f"{self._exposure_time:.1f} sec")
    
    def _on_start(self):
        """노출 시작"""
        self._is_running = True
        
        # UI 업데이트
        self.btn_start.hide()
        self.btn_stop.show()
        
        # 타이머 시작 (자동 정지)
        self._timer.start(int(self._exposure_time * 1000))
        
        # 시그널 발생
        self.exposure_start.emit(
            self._current_pattern,
            self.btn_h_flip.is_active(),
            self.btn_v_flip.is_active(),
            self._exposure_time
        )
    
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
    
    def get_flip_value(self) -> int:
        """현재 반전 설정값 반환 (NVR2+ 명령용)"""
        value = 0x00
        if self.btn_h_flip.is_active():
            value |= 0x02
        if self.btn_v_flip.is_active():
            value |= 0x04
        return value
    
    def get_pattern_value(self) -> int:
        """현재 패턴 설정값 반환 (NVR2+ 명령용)"""
        if self._current_pattern == "ramp":
            return 0x01
        else:  # checker
            return 0x07
