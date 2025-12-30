"""
VERICOM DLP 3D Printer GUI - Manual Control Page
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Signal, Qt

from pages.base_page import BasePage
from components.icon_button import ControlButton, HomeButton
from components.number_dial import DistanceSelector
from styles.colors import Colors
from styles.fonts import Fonts
from styles.icons import Icons
from styles.stylesheets import (
    get_axis_panel_style, get_axis_title_style, get_stop_button_style,
    AXIS_VALUE_STYLE
)


class AxisControlPanel(QFrame):
    """축 제어 패널"""
    
    # 이동 시그널
    move_positive = Signal(float)  # 양의 방향 이동 (거리)
    move_negative = Signal(float)  # 음의 방향 이동 (거리)
    home_axis = Signal()           # 홈 위치로
    stop_axis = Signal()           # 정지
    
    def __init__(self, axis_name: str, is_horizontal: bool = False,
                 distances: list = None, parent=None):
        super().__init__(parent)

        self._axis_name = axis_name
        self._is_horizontal = is_horizontal  # True면 좌우, False면 상하
        self._distances = distances  # 커스텀 거리 목록
        self._current_value = 0.0

        self._setup_ui()
    
    def _setup_ui(self):
        """UI 구성"""
        self.setStyleSheet(get_axis_panel_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 헤더 (축 이름 - 가운데 정렬)
        self.title_label = QLabel(self._axis_name)
        self.title_label.setStyleSheet(get_axis_title_style())
        self.title_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.title_label)
        
        # 거리 선택기
        if self._distances:
            self.distance_selector = DistanceSelector(distances=self._distances)
        else:
            self.distance_selector = DistanceSelector()
        layout.addWidget(self.distance_selector)
        
        # 제어 버튼들
        control_layout = QHBoxLayout()
        control_layout.setSpacing(12)
        control_layout.setAlignment(Qt.AlignCenter)
        
        # 홈 버튼
        self.btn_home = HomeButton(70, 28)
        self.btn_home.clicked.connect(self.home_axis.emit)
        
        # 방향 버튼들
        if self._is_horizontal:
            # 수평 (좌우)
            self.btn_negative = ControlButton(Icons.CHEVRON_LEFT, 70, 28)
            self.btn_positive = ControlButton(Icons.CHEVRON_RIGHT, 70, 28)
        else:
            # 수직 (상하)
            self.btn_positive = ControlButton(Icons.CHEVRON_UP, 70, 28)
            self.btn_negative = ControlButton(Icons.CHEVRON_DOWN, 70, 28)
        
        self.btn_positive.clicked.connect(self._on_move_positive)
        self.btn_negative.clicked.connect(self._on_move_negative)
        
        control_layout.addWidget(self.btn_home)
        control_layout.addWidget(self.btn_positive)
        control_layout.addWidget(self.btn_negative)
        
        layout.addLayout(control_layout)
        
        # 정지 버튼
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setStyleSheet(get_stop_button_style())
        self.btn_stop.setFixedHeight(45)
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setIcon(Icons.get_icon(Icons.X, 16, Colors.RED))
        self.btn_stop.clicked.connect(self.stop_axis.emit)
        
        layout.addWidget(self.btn_stop)
    
    def _on_move_positive(self):
        """양의 방향 이동"""
        distance = self.distance_selector.get_selected_distance()
        self.move_positive.emit(distance)
    
    def _on_move_negative(self):
        """음의 방향 이동"""
        distance = self.distance_selector.get_selected_distance()
        self.move_negative.emit(distance)
    
    def set_value(self, value: float):
        """현재 값 업데이트 (사용 안함)"""
        self._current_value = value


class ManualPage(BasePage):
    """수동 제어 페이지 (Z축 + X축)"""

    # 모터 제어 시그널
    z_move = Signal(float)      # Z축 이동 (+ 상승, - 하강)
    z_home = Signal()           # Z축 홈
    z_stop = Signal()           # Z축 정지

    x_move = Signal(float)      # X축(블레이드) 이동
    x_home = Signal()           # X축 홈
    x_stop = Signal()           # X축 정지

    def __init__(self, parent=None):
        super().__init__("Manual Control", show_back=True, parent=parent)
        self._is_busy = False
        self._setup_content()
    
    def _setup_content(self):
        """콘텐츠 구성"""
        # 2열 레이아웃
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(20)
        
        # Z축 패널
        self.z_panel = AxisControlPanel("Z Axis", is_horizontal=False)
        self.z_panel.move_positive.connect(lambda d: self.z_move.emit(d))
        self.z_panel.move_negative.connect(lambda d: self.z_move.emit(-d))
        self.z_panel.home_axis.connect(self.z_home.emit)
        self.z_panel.stop_axis.connect(self.z_stop.emit)
        
        # X축 패널 (블레이드) - 거리 1, 10, 100
        self.x_panel = AxisControlPanel("X Axis (Blade)", is_horizontal=True,
                                         distances=[1, 10, 100])
        self.x_panel.move_positive.connect(lambda d: self.x_move.emit(d))
        self.x_panel.move_negative.connect(lambda d: self.x_move.emit(-d))
        self.x_panel.home_axis.connect(self.x_home.emit)
        self.x_panel.stop_axis.connect(self.x_stop.emit)
        
        panels_layout.addWidget(self.z_panel)
        panels_layout.addWidget(self.x_panel)
        
        self.content_layout.addLayout(panels_layout)
    
    def update_z_position(self, value: float):
        """Z축 위치 업데이트"""
        self.z_panel.set_value(value)

    def update_x_position(self, value: float):
        """X축 위치 업데이트"""
        self.x_panel.set_value(value)

    def set_busy(self, busy: bool):
        """작업 중 상태 설정 - UI 잠금/해제"""
        self._is_busy = busy

        # 뒤로가기 버튼 비활성화
        self.header.btn_back.setEnabled(not busy)

        # 모든 제어 버튼 비활성화
        self.z_panel.btn_home.setEnabled(not busy)
        self.z_panel.btn_positive.setEnabled(not busy)
        self.z_panel.btn_negative.setEnabled(not busy)

        self.x_panel.btn_home.setEnabled(not busy)
        self.x_panel.btn_positive.setEnabled(not busy)
        self.x_panel.btn_negative.setEnabled(not busy)

        # 타이틀 변경으로 상태 표시
        if busy:
            self.header.set_title("Manual Control - Moving...")
        else:
            self.header.set_title("Manual Control")

    @property
    def is_busy(self) -> bool:
        """작업 중인지 여부"""
        return self._is_busy
