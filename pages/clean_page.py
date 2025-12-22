"""
VERICOM DLP 3D Printer GUI - Clean Page
트레이 클리닝 (전체 화면 노출)
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Signal, Qt, QTimer

from pages.base_page import BasePage
from components.number_dial import NumberDial
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import Radius


class CleanPage(BasePage):
    """트레이 클리닝 페이지"""
    
    # 클리닝 시작/정지 시그널
    clean_start = Signal(float)  # time
    clean_stop = Signal()
    
    def __init__(self, parent=None):
        super().__init__("Clean", show_back=True, parent=parent)
        
        self._clean_time = 10  # 기본 10초
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
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # 설명
        desc_label = QLabel("Full screen exposure for tray cleaning")
        desc_label.setFont(Fonts.body())
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            background-color: {Colors.BG_PRIMARY};
            border: none;
        """)
        main_layout.addWidget(desc_label)
        
        main_layout.addStretch()
        
        # === 시간 설정 ===
        time_layout = QHBoxLayout()
        time_layout.setSpacing(20)
        
        lbl_time = QLabel("Exposure Time")
        lbl_time.setFixedWidth(160)
        lbl_time.setFont(Fonts.body())
        lbl_time.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            background-color: {Colors.BG_PRIMARY};
            border: none;
        """)
        
        self.btn_time = QPushButton(f"{self._clean_time} sec")
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
        
        time_layout.addStretch()
        time_layout.addWidget(lbl_time)
        time_layout.addWidget(self.btn_time)
        time_layout.addStretch()
        
        main_layout.addLayout(time_layout)
        
        main_layout.addStretch()
        
        # === START/STOP 버튼 ===
        btn_layout = QHBoxLayout()
        
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
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addStretch()
        
        main_layout.addLayout(btn_layout)
        
        self.content_layout.addLayout(main_layout)
    
    def _show_time_dial(self):
        """시간 설정 다이얼 표시"""
        if self._is_running:
            return
        
        dial = NumberDial(
            title="Exposure Time",
            initial_value=self._clean_time,
            unit="sec",
            min_value=1,
            max_value=120,
            step=1,
            decimals=0,
            parent=self
        )

        if dial.exec():
            self._clean_time = int(dial.get_value())
            self.btn_time.setText(f"{self._clean_time} sec")
    
    def _on_start(self):
        """클리닝 시작"""
        self._is_running = True
        
        # UI 업데이트
        self.btn_start.hide()
        self.btn_stop.show()
        
        # 타이머 시작
        self._timer.start(int(self._clean_time * 1000))
        
        # 시그널 발생
        self.clean_start.emit(self._clean_time)
    
    def _on_stop(self):
        """클리닝 정지"""
        self._timer.stop()
        self._is_running = False
        
        # UI 업데이트
        self.btn_stop.hide()
        self.btn_start.show()
        
        # 시그널 발생
        self.clean_stop.emit()
    
    def _on_timer_done(self):
        """타이머 완료"""
        self._on_stop()
