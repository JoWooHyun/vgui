"""
VERICOM DLP 3D Printer GUI - Print Progress Page
인쇄 진행 상황 표시 및 제어
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QDialog, QProgressBar
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QPixmap

from pages.base_page import BasePage
from styles.colors import Colors
from styles.fonts import Fonts
from styles.icons import Icons


class ProgressInfoRow(QFrame):
    """진행 정보 표시 행 (아이콘 + 값)"""

    def __init__(self, icon_svg: str, value: str = "-", parent=None):
        super().__init__(parent)

        self.setFixedHeight(28)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: none;
                border-radius: 4px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 8, 0)
        layout.setSpacing(4)  # 아이콘-값 간격 좁힘

        # 아이콘
        self.lbl_icon = QLabel()
        self.lbl_icon.setFixedSize(18, 18)
        self.lbl_icon.setPixmap(Icons.get_pixmap(icon_svg, 16, Colors.CYAN))
        self.lbl_icon.setStyleSheet(f"background: {Colors.BG_SECONDARY}; border: none;")

        # 값 (왼쪽 정렬로 아이콘 바로 옆에 표시)
        self.lbl_value = QLabel(value)
        self.lbl_value.setFont(Fonts.body_small())
        self.lbl_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_value.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: {Colors.BG_SECONDARY};")

        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_value)
        layout.addStretch()  # 남은 공간은 오른쪽으로

    def set_value(self, value: str):
        """값 설정"""
        self.lbl_value.setText(value)


class CompletedDialog(QDialog):
    """완료 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(300, 160)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_PRIMARY};
                border: 2px solid {Colors.CYAN};
                border-radius: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # 완료 메시지
        lbl_message = QLabel("완료되었습니다!")
        lbl_message.setFont(Fonts.h2())
        lbl_message.setAlignment(Qt.AlignCenter)
        lbl_message.setStyleSheet(f"color: {Colors.CYAN}; background: transparent;")
        
        # 확인 버튼
        btn_ok = QPushButton("확인")
        btn_ok.setFixedSize(120, 48)
        btn_ok.setFont(Fonts.body())
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.CYAN};
                color: {Colors.WHITE};
                border: none;
                border-radius: 10px;
            }}
            QPushButton:pressed {{
                background-color: {Colors.CYAN_DARK};
            }}
        """)
        btn_ok.clicked.connect(self.accept)
        
        # 버튼 중앙 정렬
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        
        layout.addWidget(lbl_message)
        layout.addStretch()
        layout.addLayout(btn_layout)


class StopConfirmDialog(QDialog):
    """정지 확인 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(320, 160)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 메시지
        lbl_message = QLabel("프린트를 중지하시겠습니까?")
        lbl_message.setFont(Fonts.body())
        lbl_message.setAlignment(Qt.AlignCenter)
        lbl_message.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")
        
        # 버튼들
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        btn_cancel = QPushButton("취소")
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
            QPushButton:pressed {{
                background-color: {Colors.BG_TERTIARY};
            }}
        """)
        btn_cancel.clicked.connect(self.reject)
        
        btn_stop = QPushButton("중지")
        btn_stop.setFixedSize(120, 44)
        btn_stop.setFont(Fonts.body())
        btn_stop.setCursor(Qt.PointingHandCursor)
        btn_stop.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.RED};
                color: {Colors.WHITE};
                border: none;
                border-radius: 8px;
            }}
            QPushButton:pressed {{
                background-color: #B71C1C;
            }}
        """)
        btn_stop.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_stop)

        layout.addWidget(lbl_message)
        layout.addStretch()
        layout.addLayout(btn_layout)


class StoppedDialog(QDialog):
    """정지 완료 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(300, 160)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_PRIMARY};
                border: 2px solid {Colors.AMBER};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 메시지
        lbl_message = QLabel("정지 완료!")
        lbl_message.setFont(Fonts.h2())
        lbl_message.setAlignment(Qt.AlignCenter)
        lbl_message.setStyleSheet(f"color: {Colors.AMBER}; background: transparent;")

        # 확인 버튼
        btn_ok = QPushButton("확인")
        btn_ok.setFixedSize(120, 48)
        btn_ok.setFont(Fonts.body())
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.AMBER};
                color: {Colors.WHITE};
                border: none;
                border-radius: 10px;
            }}
            QPushButton:pressed {{
                background-color: #E68A00;
            }}
        """)
        btn_ok.clicked.connect(self.accept)

        # 버튼 중앙 정렬
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()

        layout.addWidget(lbl_message)
        layout.addStretch()
        layout.addLayout(btn_layout)


class ErrorDialog(QDialog):
    """에러 다이얼로그"""

    def __init__(self, message: str, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(360, 180)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_PRIMARY};
                border: 2px solid {Colors.RED};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 에러 제목
        lbl_title = QLabel("오류")
        lbl_title.setFont(Fonts.h2())
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(f"color: {Colors.RED}; background: transparent;")

        # 에러 메시지
        lbl_message = QLabel(message)
        lbl_message.setFont(Fonts.body_small())
        lbl_message.setAlignment(Qt.AlignCenter)
        lbl_message.setWordWrap(True)
        lbl_message.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent;")

        # 확인 버튼
        btn_ok = QPushButton("확인")
        btn_ok.setFixedSize(120, 48)
        btn_ok.setFont(Fonts.body())
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.RED};
                color: {Colors.WHITE};
                border: none;
                border-radius: 10px;
            }}
            QPushButton:pressed {{
                background-color: #B71C1C;
            }}
        """)
        btn_ok.clicked.connect(self.accept)

        # 버튼 중앙 정렬
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_message)
        layout.addStretch()
        layout.addLayout(btn_layout)


class PrintProgressPage(BasePage):
    """프린트 진행 페이지"""

    # 시그널 (Worker 제어용)
    pause_requested = Signal()
    resume_requested = Signal()
    stop_requested = Signal()
    go_home = Signal()
    z_home_requested = Signal()  # Z축 홈 요청

    # 상태 상수
    STATUS_PRINTING = "printing"
    STATUS_PAUSED = "paused"
    STATUS_STOPPING = "stopping"
    STATUS_COMPLETED = "completed"
    STATUS_ERROR = "error"
    STATUS_STOPPED = "stopped"
    
    def __init__(self, parent=None):
        super().__init__("Printing...", show_back=False, parent=parent)
        
        self._status = self.STATUS_PRINTING
        self._file_path = ""
        self._thumbnail = None
        self._current_layer = 0
        self._total_layers = 0
        self._elapsed_sec = 0
        self._blade_speed = 1500
        self._led_power = 100
        self._total_estimated_time = 0
        
        # 경과 시간 타이머
        self._elapsed_timer = QTimer()
        self._elapsed_timer.timeout.connect(self._on_elapsed_tick)
        
        self._setup_content()
    
    def _setup_content(self):
        """콘텐츠 구성"""
        # === 상단: 레이어 이미지 + 정보 ===
        top_layout = QHBoxLayout()
        top_layout.setSpacing(16)

        # 왼쪽: 현재 레이어 이미지 (큰 프리뷰)
        self.preview_frame = QFrame()
        self.preview_frame.setFixedSize(280, 280)
        self.preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: 3px solid {Colors.CYAN};
                border-radius: 12px;
            }}
        """)

        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(4, 4, 4, 4)
        preview_layout.setAlignment(Qt.AlignCenter)

        self.lbl_layer_image = QLabel()
        self.lbl_layer_image.setFixedSize(270, 270)
        self.lbl_layer_image.setAlignment(Qt.AlignCenter)
        self.lbl_layer_image.setStyleSheet(f"background-color: transparent; border: none;")
        self.lbl_layer_image.setPixmap(Icons.get_pixmap(Icons.FILE, 64, Colors.TEXT_DISABLED))

        preview_layout.addWidget(self.lbl_layer_image)

        # 오른쪽: 정보 세로 나열
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        info_layout.setAlignment(Qt.AlignTop)

        # 정보 행들 (세로 나열)
        self.row_bottom_exposure = ProgressInfoRow(Icons.EXPOSURE_BOTTOM)  # 바닥 노출
        self.row_normal_exposure = ProgressInfoRow(Icons.EXPOSURE_NORMAL)  # 일반 노출
        self.row_layer_height = ProgressInfoRow(Icons.RULER)  # 레이어 높이
        self.row_layer = ProgressInfoRow(Icons.STACK)  # 현재/총 레이어
        self.row_bottom_layers = ProgressInfoRow(Icons.BOTTOM_LAYERS)  # 바닥 레이어 수
        self.row_blade_speed = ProgressInfoRow(Icons.BLADE_SPEED)  # 블레이드 속도
        self.row_led_power = ProgressInfoRow(Icons.LED_POWER)  # LED 파워
        self.row_elapsed = ProgressInfoRow(Icons.CLOCK)  # 경과 시간
        self.row_total_time = ProgressInfoRow(Icons.HOURGLASS)  # 총 예상 시간

        info_layout.addWidget(self.row_bottom_exposure)
        info_layout.addWidget(self.row_normal_exposure)
        info_layout.addWidget(self.row_layer_height)
        info_layout.addWidget(self.row_layer)
        info_layout.addWidget(self.row_bottom_layers)
        info_layout.addWidget(self.row_blade_speed)
        info_layout.addWidget(self.row_led_power)
        info_layout.addWidget(self.row_elapsed)
        info_layout.addWidget(self.row_total_time)
        info_layout.addStretch()

        top_layout.addWidget(self.preview_frame)
        top_layout.addLayout(info_layout, 1)

        self.content_layout.addLayout(top_layout, 1)

        # === 하단: 파일명 + 진행바 + 버튼 ===
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(12)

        # 파일명
        self.lbl_filename = QLabel("filename.zip")
        self.lbl_filename.setFont(Fonts.h3())
        self.lbl_filename.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        self.lbl_filename.setAlignment(Qt.AlignCenter)

        # 진행률 바 + 퍼센트
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(12)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(28)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.BG_TERTIARY};
                border: none;
                border-radius: 8px;
            }}
            QProgressBar::chunk {{
                background-color: {Colors.CYAN};
                border-radius: 8px;
            }}
        """)

        self.lbl_percent = QLabel("0%")
        self.lbl_percent.setFont(Fonts.h2())
        self.lbl_percent.setFixedWidth(60)
        self.lbl_percent.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_percent.setStyleSheet(f"color: {Colors.CYAN}; font-weight: 600;")

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.lbl_percent)

        bottom_layout.addWidget(self.lbl_filename)
        bottom_layout.addLayout(progress_layout)

        # 버튼들 (프린팅 중: PAUSE/STOP, 종료 후: GUI홈/Z축홈)
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(20)

        # PAUSE/RESUME 버튼
        self.btn_pause = QPushButton("PAUSE")
        self.btn_pause.setFixedSize(120, 48)
        self.btn_pause.setFont(Fonts.body())
        self.btn_pause.setCursor(Qt.PointingHandCursor)
        self._set_pause_button_style()
        self.btn_pause.clicked.connect(self._on_pause_clicked)

        # STOP 버튼
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setFixedSize(120, 48)
        self.btn_stop.setFont(Fonts.body())
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                color: {Colors.RED};
                border: 2px solid {Colors.RED};
                border-radius: 10px;
            }}
            QPushButton:pressed {{
                background-color: {Colors.RED};
                color: {Colors.WHITE};
            }}
        """)
        self.btn_stop.clicked.connect(self._on_stop_clicked)

        # GUI 홈 버튼 (종료 후 표시)
        self.btn_gui_home = QPushButton("GUI 홈")
        self.btn_gui_home.setFixedSize(120, 48)
        self.btn_gui_home.setFont(Fonts.body())
        self.btn_gui_home.setCursor(Qt.PointingHandCursor)
        self.btn_gui_home.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.CYAN};
                color: {Colors.WHITE};
                border: none;
                border-radius: 10px;
            }}
            QPushButton:pressed {{
                background-color: {Colors.CYAN_DARK};
            }}
        """)
        self.btn_gui_home.clicked.connect(self._on_gui_home_clicked)
        self.btn_gui_home.hide()

        # Z축 홈 버튼 (종료 후 표시)
        self.btn_z_home = QPushButton("Z축 홈")
        self.btn_z_home.setFixedSize(120, 48)
        self.btn_z_home.setFont(Fonts.body())
        self.btn_z_home.setCursor(Qt.PointingHandCursor)
        self.btn_z_home.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                color: {Colors.CYAN};
                border: 2px solid {Colors.CYAN};
                border-radius: 10px;
            }}
            QPushButton:pressed {{
                background-color: {Colors.CYAN};
                color: {Colors.WHITE};
            }}
        """)
        self.btn_z_home.clicked.connect(self._on_z_home_clicked)
        self.btn_z_home.hide()

        self.btn_layout.addStretch()
        self.btn_layout.addWidget(self.btn_pause)
        self.btn_layout.addWidget(self.btn_stop)
        self.btn_layout.addWidget(self.btn_gui_home)
        self.btn_layout.addWidget(self.btn_z_home)
        self.btn_layout.addStretch()

        bottom_layout.addLayout(self.btn_layout)

        self.content_layout.addLayout(bottom_layout)
    
    def _set_pause_button_style(self):
        """PAUSE 버튼 스타일 (Amber)"""
        self.btn_pause.setText("PAUSE")
        self.btn_pause.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.AMBER};
                color: {Colors.WHITE};
                border: none;
                border-radius: 10px;
            }}
            QPushButton:pressed {{
                background-color: #E68A00;
            }}
        """)

    def _set_resume_button_style(self):
        """RESUME 버튼 스타일 (Cyan)"""
        self.btn_pause.setText("RESUME")
        self.btn_pause.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.CYAN};
                color: {Colors.WHITE};
                border: none;
                border-radius: 10px;
            }}
            QPushButton:pressed {{
                background-color: {Colors.CYAN_DARK};
            }}
        """)
    
    def _on_pause_clicked(self):
        """PAUSE/RESUME 버튼 클릭"""
        if self._status == self.STATUS_PRINTING:
            self._status = self.STATUS_PAUSED
            self._elapsed_timer.stop()
            self._set_resume_button_style()
            self._update_title("Paused")
            self.pause_requested.emit()
        elif self._status == self.STATUS_PAUSED:
            self._status = self.STATUS_PRINTING
            self._elapsed_timer.start(1000)
            self._set_pause_button_style()
            self._update_title("Printing...")
            self.resume_requested.emit()
    
    def _on_stop_clicked(self):
        """STOP 버튼 클릭"""
        dialog = StopConfirmDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._status = self.STATUS_STOPPING
            self._elapsed_timer.stop()
            self._update_title("Stopping...")
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.stop_requested.emit()

    def _on_gui_home_clicked(self):
        """GUI 홈 버튼 클릭 - 메인 페이지로 이동"""
        self.go_home.emit()

    def _on_z_home_clicked(self):
        """Z축 홈 버튼 클릭 - Z축 홈 복귀 후 메인 페이지로 이동"""
        self.z_home_requested.emit()
        self.go_home.emit()

    def _show_finish_buttons(self):
        """종료 버튼 표시 (PAUSE/STOP 숨기고 GUI홈/Z축홈 표시)"""
        self.btn_pause.hide()
        self.btn_stop.hide()
        self.btn_gui_home.show()
        self.btn_z_home.show()

    def _show_printing_buttons(self):
        """프린팅 버튼 표시 (GUI홈/Z축홈 숨기고 PAUSE/STOP 표시)"""
        self.btn_gui_home.hide()
        self.btn_z_home.hide()
        self.btn_pause.show()
        self.btn_stop.show()
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)

    def _update_title(self, title: str):
        """헤더 타이틀 업데이트"""
        self.header.set_title(title)
    
    def _on_elapsed_tick(self):
        """1초마다 경과 시간 증가"""
        self._elapsed_sec += 1
        self._update_time_display()
    
    def _update_time_display(self):
        """시간 표시 업데이트 (경과 시간만 업데이트, 총 예상 시간은 고정)"""
        # 경과 시간만 업데이트
        self.row_elapsed.set_value(self._format_time(self._elapsed_sec))
    
    def _format_time(self, seconds: int) -> str:
        """초를 MM:SS 또는 HH:MM:SS 형식으로 변환"""
        if seconds >= 3600:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:02d}:{secs:02d}"

    def _calculate_total_time(self, gcode_time: int, total_layers: int,
                               blade_speed: int) -> int:
        """총 예상 시간 계산 (블레이드 시간 포함)

        Args:
            gcode_time: run.gcode의 예상 시간 (초)
            total_layers: 총 레이어 수
            blade_speed: 블레이드 속도 (Gcode값, GUI = blade_speed / 50)

        Returns:
            총 예상 시간 (초)
        """
        BLADE_ROUND_TRIP = 250.0  # mm (0→125→0 왕복)

        # Gcode값을 GUI값(mm/s)으로 변환
        blade_speed_mm_s = blade_speed / 50.0

        if blade_speed_mm_s <= 0:
            blade_speed_mm_s = 30.0  # 기본값

        # 블레이드 1회 왕복 시간
        blade_time_per_layer = BLADE_ROUND_TRIP / blade_speed_mm_s

        # 총 블레이드 시간
        total_blade_time = blade_time_per_layer * total_layers

        return int(gcode_time + total_blade_time)

    # === Public API (Worker에서 호출) ===
    
    def set_print_info(self, file_path: str, thumbnail: QPixmap,
                       total_layers: int, blade_speed: int, led_power: int,
                       estimated_time: int = 0, layer_height: float = 0.0,
                       bottom_exposure: float = 0.0, normal_exposure: float = 0.0,
                       bottom_layer_count: int = 0):
        """프린트 정보 설정 (시작 시 호출)

        Args:
            file_path: 파일 경로
            thumbnail: 썸네일 이미지
            total_layers: 총 레이어 수
            blade_speed: 블레이드 속도 (mm/min)
            led_power: LED 파워 (%)
            estimated_time: 예상 시간 (초)
            layer_height: 레이어 높이 (mm)
            bottom_exposure: 바닥 노출 시간 (초)
            normal_exposure: 일반 노출 시간 (초)
            bottom_layer_count: 바닥 레이어 개수
        """
        self._file_path = file_path
        self._total_layers = total_layers
        self._blade_speed = blade_speed
        self._led_power = led_power
        self._current_layer = 0
        self._elapsed_sec = 0
        self._status = self.STATUS_PRINTING

        # UI 업데이트
        filename = os.path.basename(file_path)
        self.lbl_filename.setText(filename)

        # 초기 레이어 이미지 (썸네일 또는 기본 아이콘)
        if thumbnail:
            scaled = thumbnail.scaled(270, 270, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_layer_image.setPixmap(scaled)
        else:
            self.lbl_layer_image.setPixmap(Icons.get_pixmap(Icons.FILE, 64, Colors.TEXT_DISABLED))

        # 총 예상 시간 계산 (블레이드 시간 포함)
        total_estimated_time = self._calculate_total_time(
            estimated_time, total_layers, blade_speed
        )
        self._total_estimated_time = total_estimated_time

        # 왼쪽 열: 진행 정보
        self.row_layer.set_value(f"0 / {total_layers}")
        self.row_elapsed.set_value("00:00")
        self.row_total_time.set_value(self._format_time(total_estimated_time) if total_estimated_time > 0 else "--:--")

        # 중앙 열: 레이어 정보
        self.row_layer_height.set_value(f"{layer_height:.3f} mm" if layer_height > 0 else "-")
        self.row_bottom_exposure.set_value(f"{bottom_exposure:.1f} s" if bottom_exposure > 0 else "-")
        self.row_normal_exposure.set_value(f"{normal_exposure:.1f} s" if normal_exposure > 0 else "-")

        # 오른쪽 열: 설정 정보
        self.row_bottom_layers.set_value(f"{bottom_layer_count}" if bottom_layer_count > 0 else "-")
        self.row_blade_speed.set_value(f"{blade_speed / 50:.0f} mm/s")  # mm/min을 mm/s로 표시
        self.row_led_power.set_value(f"{led_power} %")

        self.progress_bar.setValue(0)
        self.lbl_percent.setText("0%")

        # 버튼 초기화 (프린팅 버튼 표시)
        self._show_printing_buttons()
        self._set_pause_button_style()
        self._update_title("Printing...")

        # 타이머 시작
        self._elapsed_timer.start(1000)
    
    def update_progress(self, current_layer: int, total_layers: int):
        """진행률 업데이트 (Worker에서 호출)"""
        self._current_layer = current_layer
        self._total_layers = total_layers

        # 퍼센트 계산
        if total_layers > 0:
            percent = int((current_layer / total_layers) * 100)
        else:
            percent = 0

        self.progress_bar.setValue(percent)
        self.lbl_percent.setText(f"{percent}%")
        self.row_layer.set_value(f"{current_layer} / {total_layers}")

        self._update_time_display()

    def update_layer_image(self, pixmap: QPixmap):
        """현재 레이어 이미지 업데이트 (Worker에서 호출)"""
        if pixmap:
            scaled = pixmap.scaled(270, 270, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_layer_image.setPixmap(scaled)
    
    def show_completed(self):
        """완료 - 다이얼로그 표시 후 종료 버튼으로 전환"""
        self._status = self.STATUS_COMPLETED
        self._elapsed_timer.stop()
        self._update_title("Completed")

        self.progress_bar.setValue(100)
        self.lbl_percent.setText("100%")

        # 완료 다이얼로그 표시
        dialog = CompletedDialog(self)
        dialog.exec()

        # 종료 버튼 표시
        self._show_finish_buttons()

    def show_stopped(self):
        """정지됨 - 다이얼로그 표시 후 종료 버튼으로 전환"""
        self._status = self.STATUS_STOPPED
        self._elapsed_timer.stop()
        self._update_title("Stopped")

        # 정지 완료 다이얼로그
        dialog = StoppedDialog(self)
        dialog.exec()

        # 종료 버튼 표시
        self._show_finish_buttons()

    def show_error(self, message: str):
        """에러 - 다이얼로그 표시 후 종료 버튼으로 전환"""
        self._status = self.STATUS_ERROR
        self._elapsed_timer.stop()
        self._update_title("Error")

        # 에러 다이얼로그 표시
        dialog = ErrorDialog(message, self)
        dialog.exec()

        # 종료 버튼 표시
        self._show_finish_buttons()

    def get_status(self) -> str:
        """현재 상태 반환"""
        return self._status
