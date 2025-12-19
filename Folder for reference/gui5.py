#!/usr/bin/env python3
"""
DLP 3D 프린터 메인 GUI 시스템 (gui5.py)
- ZIP 파일별 run.gcode 파라미터 동적 적용
- 실제 3D 레진프린터 동작 구현
- 모터 제어 및 프로젝션 통합
"""

import ctypes
import sys
import os
import zipfile
import io
import json
import subprocess
import time
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QPushButton, QLabel, QLineEdit,
    QHBoxLayout, QVBoxLayout,
    QGridLayout, QStackedWidget, QTextEdit,
    QProgressBar, QDialog, QFileDialog,
    QMessageBox
)
from PySide6.QtGui import QIcon, QFont, QPixmap
from PySide6.QtCore import Qt, QSize, QTimer

from dlp_simple_slideshow import run_slideshow, extract_print_parameters

# ======================= 초기 설정 =======================
print("NVR2+ 통합 DLP 3D 프린터 컨트롤러 시작")

# Moonraker API URL 설정 (모터 제어용)
MOONRAKER_URL = "http://localhost:7125"

# CyUSBSerial 라이브러리 로드
try:
    print("CyUSBSerial 라이브러리 로드 시도")
    cy_lib = ctypes.CDLL("libcyusbserial.so")
    print("라이브러리 로드 성공")
except Exception as e:
    print(f"라이브러리 로드 실패: {e}")
    sys.exit(1)

# ======================= 구조체 정의 =======================
class CY_I2C_DATA_CONFIG(ctypes.Structure):
    """Cypress I2C 데이터 설정 구조체"""
    _fields_ = [
        ("slaveAddress", ctypes.c_ubyte),
        ("isStopBit", ctypes.c_bool),
        ("isNakBit", ctypes.c_bool)
    ]

class CY_DATA_BUFFER(ctypes.Structure):
    """Cypress 데이터 버퍼 구조체"""
    _fields_ = [
        ("buffer", ctypes.POINTER(ctypes.c_ubyte)),
        ("length", ctypes.c_uint32),
        ("transferCount", ctypes.c_uint32)
    ]

# CY_HANDLE 정의
CY_HANDLE = ctypes.c_void_p

# ======================= 스타일 정의 =======================
BUTTON_STYLE = """
    QPushButton {
        background-color: #5B9BD5;
        color: white;
        border-radius: 5px;
        font-size: 14px;
        font-weight: bold;
        padding: 10px;
    }
    QPushButton:pressed {
        background-color: #4A86C5;
    }
    QPushButton:hover {
        background-color: #6BA6E0;
    }
"""

SELECTED_BUTTON_STYLE = """
    QPushButton {
        background-color: #FFD700;
        color: black;
        border: 2px solid #FFA500;
        border-radius: 5px;
        font-size: 14px;
        font-weight: bold;
        padding: 10px;
    }
    QPushButton:pressed {
        background-color: #FFC700;
    }
"""

STOP_BUTTON_STYLE = """
    QPushButton {
        background-color: #FF4444;
        color: white;
        border-radius: 5px;
        font-size: 16px;
        font-weight: bold;
        padding: 12px;
    }
    QPushButton:pressed {
        background-color: #CC3333;
    }
"""

# ======================= 정지 확인 대화상자 =======================
class StopConfirmationDialog(QDialog):
    """프린팅 정지 확인 대화상자"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("정지 확인")
        self.setFixedSize(300, 150)
        self.setModal(True)
        # 대화상자를 최상위로 표시
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self._build_ui()

    def _build_ui(self):
        """UI 구성"""
        message_label = QLabel("프린팅을 정지하시겠습니까?")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setFont(QFont("Arial", 14, QFont.Bold))
        message_label.setStyleSheet("color: red; margin: 10px;")

        # 버튼 생성
        self.btn_yes = QPushButton("예")
        self.btn_no = QPushButton("아니오")
        
        # 버튼 스타일 및 크기 설정
        for btn in [self.btn_yes, self.btn_no]:
            btn.setFixedSize(100, 40)
            btn.setStyleSheet(BUTTON_STYLE)

        # 버튼 이벤트 연결
        self.btn_yes.clicked.connect(self.accept)
        self.btn_no.clicked.connect(self.reject)

        # 레이아웃 구성
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_yes)
        button_layout.addWidget(self.btn_no)

        main_layout = QVBoxLayout()
        main_layout.addWidget(message_label)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

# ======================= 숫자 키패드 대화상자 =======================
class NumericKeypadDialog(QDialog):
    """터치스크린용 숫자 키패드 대화상자"""
    def __init__(self, parent=None, title="숫자 입력", default_value="", unit=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(320, 400)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        self.unit = unit
        self.input_value = default_value
        self._build_ui()

    def _build_ui(self):
        """UI 구성"""
        # 타이틀
        title_label = QLabel(self.windowTitle())
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #2C3E50; margin: 5px;")

        # 입력값 표시 영역
        self.display_label = QLabel(f"{self.input_value} {self.unit}")
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.display_label.setStyleSheet("""
            background-color: white;
            border: 2px solid #5B9BD5;
            border-radius: 5px;
            padding: 10px;
            color: #333;
            min-height: 40px;
        """)

        # 숫자 버튼 스타일
        number_button_style = """
            QPushButton {
                background-color: #5B9BD5;
                color: white;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:pressed {
                background-color: #4A86C5;
            }
        """

        # 백스페이스 버튼 스타일
        backspace_button_style = """
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:pressed {
                background-color: #E68900;
            }
        """

        # 확인 버튼 스타일
        confirm_button_style = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:pressed {
                background-color: #45A049;
            }
        """

        # 취소 버튼 스타일
        cancel_button_style = """
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:pressed {
                background-color: #757575;
            }
        """

        # 숫자 버튼 그리드 (3x4)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)

        # 숫자 버튼 1-9
        self.number_buttons = []
        for i in range(1, 10):
            btn = QPushButton(str(i))
            btn.setFixedSize(70, 60)
            btn.setStyleSheet(number_button_style)
            btn.clicked.connect(lambda checked, num=i: self._append_number(num))
            self.number_buttons.append(btn)
            
            row = (i - 1) // 3
            col = (i - 1) % 3
            grid_layout.addWidget(btn, row, col)

        # 백스페이스 버튼
        btn_backspace = QPushButton("⌫")
        btn_backspace.setFixedSize(70, 60)
        btn_backspace.setStyleSheet(backspace_button_style)
        btn_backspace.clicked.connect(self._backspace)
        grid_layout.addWidget(btn_backspace, 3, 0)

        # 0 버튼
        btn_zero = QPushButton("0")
        btn_zero.setFixedSize(70, 60)
        btn_zero.setStyleSheet(number_button_style)
        btn_zero.clicked.connect(lambda: self._append_number(0))
        grid_layout.addWidget(btn_zero, 3, 1)

        # 확인 버튼
        btn_confirm = QPushButton("✓")
        btn_confirm.setFixedSize(70, 60)
        btn_confirm.setStyleSheet(confirm_button_style)
        btn_confirm.clicked.connect(self._confirm)
        grid_layout.addWidget(btn_confirm, 3, 2)

        # 취소 버튼 (하단)
        btn_cancel = QPushButton("취소")
        btn_cancel.setFixedSize(220, 45)
        btn_cancel.setStyleSheet(cancel_button_style)
        btn_cancel.clicked.connect(self.reject)

        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.display_label)
        main_layout.addSpacing(10)
        main_layout.addLayout(grid_layout)
        main_layout.addSpacing(10)
        main_layout.addWidget(btn_cancel, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

    def _append_number(self, num):
        """숫자 추가"""
        # 최대 6자리까지만 입력 가능
        if len(self.input_value) < 6:
            self.input_value += str(num)
            self.display_label.setText(f"{self.input_value} {self.unit}")

    def _backspace(self):
        """마지막 숫자 삭제"""
        if len(self.input_value) > 0:
            self.input_value = self.input_value[:-1]
            self.display_label.setText(f"{self.input_value} {self.unit}" if self.input_value else f"0 {self.unit}")

    def _confirm(self):
        """확인 - 입력값 검증 후 닫기"""
        if not self.input_value or self.input_value == "0":
            QMessageBox.warning(self, "입력 오류", "0보다 큰 값을 입력해주세요.")
            return
        
        self.accept()

    def get_value(self):
        """입력된 값 반환"""
        return self.input_value if self.input_value else "0"

# ======================= 홈 메뉴 클래스 =======================
class HomeMenu(QWidget):
    """메인 홈 메뉴"""
    def __init__(self, switch_to_tools_callback):
        super().__init__()
        self.switch_to_tools = switch_to_tools_callback
        self._build_ui()

    def _build_ui(self):
        """홈 메뉴 UI 구성"""
        # 타이틀 라벨
        title = QLabel("DLP 3D 프린터")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #2C3E50; margin: 20px;")

        # 메인 버튼들 생성
        btn_print = QPushButton("Print")
        btn_system = QPushButton("System")
        btn_tools = QPushButton("Tools")

        # 버튼 크기 및 스타일 설정
        for btn in [btn_print, btn_system, btn_tools]:
            btn.setFixedSize(200, 80)
            btn.setFont(QFont("Arial", 16, QFont.Bold))
            btn.setStyleSheet(BUTTON_STYLE)

        # 버튼 이벤트 연결
        btn_tools.clicked.connect(self.switch_to_tools)

        # 레이아웃 구성
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(btn_print)
        button_layout.addWidget(btn_system)
        button_layout.addWidget(btn_tools)
        button_layout.addStretch()

        main_layout = QVBoxLayout()
        main_layout.addStretch()
        main_layout.addWidget(title)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

# ======================= 도구 메뉴 클래스 =======================
class ToolsMenu(QWidget):
    """도구 메뉴"""
    def __init__(self, return_to_home_callback):
        super().__init__()
        self.return_to_home = return_to_home_callback
        self._build_ui()

    def _build_ui(self):
        """도구 메뉴 UI 구성"""
        # 타이틀
        title = QLabel("Tools Menu")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Bold))

        # 버튼들
        btn_move_z = QPushButton("Move Z")
        btn_calibration = QPushButton("Calibration")
        btn_settings = QPushButton("Settings")
        btn_back = QPushButton("Back")

        # 버튼 설정
        for btn in [btn_move_z, btn_calibration, btn_settings, btn_back]:
            btn.setFixedSize(180, 60)
            btn.setStyleSheet(BUTTON_STYLE)

        # 이벤트 연결
        btn_back.clicked.connect(self.return_to_home)

        # 레이아웃
        grid = QGridLayout()
        grid.addWidget(btn_move_z, 0, 0)
        grid.addWidget(btn_calibration, 0, 1)
        grid.addWidget(btn_settings, 1, 0)
        grid.addWidget(btn_back, 1, 1)

        main_layout = QVBoxLayout()
        main_layout.addWidget(title)
        main_layout.addLayout(grid)

        self.setLayout(main_layout)

# ======================= Z축 이동 메뉴 클래스 =======================
class MoveZMenu(QWidget):
    """Z축 이동 메뉴"""
    def __init__(self, return_to_tools_callback):
        super().__init__()
        self.return_to_tools = return_to_tools_callback
        self.selected_step = "1mm"  # 기본 스텝
        self._build_ui()

    def _build_ui(self):
        """Z축 이동 메뉴 UI 구성"""
        title = QLabel("Move Z Axis")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Bold))

        # 스텝 선택 버튼들
        self.step_buttons = []
        btn_01 = QPushButton("0.1mm")
        btn_1 = QPushButton("1mm") 
        btn_10 = QPushButton("10mm")
        
        self.step_buttons = [btn_01, btn_1, btn_10]
        
        for btn in self.step_buttons:
            btn.setFixedSize(100, 40)
            btn.setStyleSheet(BUTTON_STYLE)
            btn.clicked.connect(lambda _, b=btn: self._select_step(b))

        # 기본 선택
        btn_1.setStyleSheet(SELECTED_BUTTON_STYLE)

        # 이동 버튼들
        btn_up = QPushButton("↑ UP")
        btn_down = QPushButton("↓ DOWN")
        btn_home = QPushButton("🏠 HOME")
        btn_back = QPushButton("← Back")

        for btn in [btn_up, btn_down, btn_home, btn_back]:
            btn.setFixedSize(120, 60)
            btn.setStyleSheet(BUTTON_STYLE)

        # 이벤트 연결
        btn_up.clicked.connect(self._move_up)
        btn_down.clicked.connect(self._move_down)
        btn_home.clicked.connect(self._home_z)
        btn_back.clicked.connect(self.return_to_tools)

        # 레이아웃
        step_layout = QHBoxLayout()
        for btn in self.step_buttons:
            step_layout.addWidget(btn)

        move_layout = QGridLayout()
        move_layout.addWidget(btn_up, 0, 1)
        move_layout.addWidget(btn_down, 2, 1)
        move_layout.addWidget(btn_home, 1, 0)
        move_layout.addWidget(btn_back, 1, 2)

        main_layout = QVBoxLayout()
        main_layout.addWidget(title)
        main_layout.addLayout(step_layout)
        main_layout.addLayout(move_layout)

        self.setLayout(main_layout)

    def _select_step(self, button):
        """스텝 선택"""
        # 모든 버튼 기본 스타일로 복원
        for btn in self.step_buttons:
            btn.setStyleSheet(BUTTON_STYLE)
        
        # 선택된 버튼 강조
        button.setStyleSheet(SELECTED_BUTTON_STYLE)
        self.selected_step = button.text()

    def _move_up(self):
        """Z축 상승"""
        step_value = float(self.selected_step.replace("mm", ""))
        self._send_z_command(f"G91\nG1 Z{step_value} F300\nG90")

    def _move_down(self):
        """Z축 하강"""
        step_value = float(self.selected_step.replace("mm", ""))
        self._send_z_command(f"G91\nG1 Z-{step_value} F300\nG90")

    def _home_z(self):
        """Z축 홈"""
        self._send_z_command("G28 Z")

    def _send_z_command(self, gcode):
        """G-code 명령 전송"""
        try:
            url = f"{MOONRAKER_URL}/printer/gcode/script"
            data = {"script": gcode}
            response = requests.post(url, json=data, timeout=5)
            print(f"Z축 명령 전송: {gcode}")
        except Exception as e:
            print(f"Z축 제어 오류: {e}")

# ======================= 프린트 메뉴 클래스 =======================
class PrintMenu(QWidget):
    """프린트 파일 선택 메뉴"""
    def __init__(self, return_to_home_callback):
        super().__init__()
        self.return_to_home = return_to_home_callback
        self.file_paths = []
        self.current_page = 0
        self.items_per_page = 6
        self.selected_button_index = None
        self.usb_devices = []
        
        # USB 모니터링 타이머
        self.usb_timer = QTimer()
        self.usb_timer.timeout.connect(self.poll_usb)
        
        self._build_ui()

    def _build_ui(self):
        """프린트 메뉴 UI 구성"""
        # 타이틀
        title = QLabel("Select Print File")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Bold))

        # USB 상태 라벨
        self.usb_status_label = QLabel("USB 상태: 확인 중...")
        self.usb_status_label.setStyleSheet("color: blue; font-size: 12px;")

        # 파일 버튼들 (2x3 그리드)
        self.file_buttons = []
        self.file_labels = []
        
        file_grid = QGridLayout()
        for i in range(6):
            btn = QPushButton()
            btn.setFixedSize(120, 80)
            btn.setStyleSheet(BUTTON_STYLE)
            btn.clicked.connect(lambda _, idx=i: self.on_file_clicked(idx))
            
            label = QLabel("")
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            label.setMaximumWidth(120)
            
            self.file_buttons.append(btn)
            self.file_labels.append(label)
            
            row, col = divmod(i, 3)
            file_grid.addWidget(btn, row * 2, col)
            file_grid.addWidget(label, row * 2 + 1, col)

        # 네비게이션 버튼들
        self.btn_prev = QPushButton("◀ 이전")
        self.btn_next = QPushButton("다음 ▶")
        self.btn_enter = QPushButton("선택")
        self.btn_back = QPushButton("뒤로")

        for btn in [self.btn_prev, self.btn_next, self.btn_enter, self.btn_back]:
            btn.setFixedSize(100, 40)
            btn.setStyleSheet(BUTTON_STYLE)

        # 이벤트 연결
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)
        self.btn_back.clicked.connect(self.return_to_home)

        # 네비게이션 레이아웃
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        nav_layout.addWidget(self.btn_enter)
        nav_layout.addWidget(self.btn_back)

        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.addWidget(title)
        main_layout.addWidget(self.usb_status_label)
        main_layout.addLayout(file_grid)
        main_layout.addLayout(nav_layout)

        self.setLayout(main_layout)

    def start_polling(self):
        """USB 폴링 시작"""
        self.detect_usb_devices()
        self.usb_timer.start(2000)  # 2초마다

    def stop_polling(self):
        """USB 폴링 중지"""
        self.usb_timer.stop()
    
    def update_usb_file_list(self):
        """USB 파일 목록 업데이트"""
        self.file_paths = []

        for usb_path in self.usb_devices:
            if os.path.isdir(usb_path):
                try:
                    entries = sorted(os.listdir(usb_path))
                    for fname in entries:
                        full = os.path.join(usb_path, fname)
                        if os.path.isfile(full):
                            ext = os.path.splitext(fname)[1].lower()
                            # DLP 프린터 파일만 필터링
                            if ext in ['.zip', '.dlp', '.photon', '.ctb']:
                                self.file_paths.append(full)
                except PermissionError:
                    continue

        self.show_page(0)

    def show_page(self, page: int):
        """페이지 표시"""
        self.current_page = page
        start = page * self.items_per_page
        end = start + self.items_per_page
        files = self.file_paths[start:end]

        for idx in range(self.items_per_page):
            btn = self.file_buttons[idx]
            lbl = self.file_labels[idx]
            btn.setStyleSheet(BUTTON_STYLE)

            if idx < len(files):
                name = os.path.basename(files[idx])
                lbl.setText(name)
                ext = os.path.splitext(name)[1].lower()

                # ZIP 파일의 경우 미리보기 이미지 표시
                if ext == ".zip":
                    try:
                        with zipfile.ZipFile(files[idx], 'r') as z:
                            if "preview_cropping.png" in z.namelist():
                                data = z.read("preview_cropping.png")
                                pix = QPixmap()
                                pix.loadFromData(data)
                                btn.setIcon(QIcon(pix))
                            else:
                                btn.setIcon(QIcon("/home/veri/GUI/icons/file.png"))
                    except:
                        btn.setIcon(QIcon("/home/veri/GUI/icons/file.png"))
                else:
                    btn.setIcon(QIcon("/home/veri/GUI/icons/file.png"))
            else:
                lbl.setText("")
                btn.setIcon(QIcon())

        # 선택된 버튼 강조
        if self.selected_button_index is not None:
            rel = self.selected_button_index - start
            if 0 <= rel < self.items_per_page:
                self.file_buttons[rel].setStyleSheet(SELECTED_BUTTON_STYLE)

    def on_file_clicked(self, idx: int):
        """파일 버튼 클릭"""
        abs_index = self.current_page * self.items_per_page + idx
        if abs_index < len(self.file_paths):
            self.selected_button_index = abs_index
            self.show_page(self.current_page)

    def prev_page(self):
        """이전 페이지"""
        if self.current_page > 0:
            self.show_page(self.current_page - 1)

    def next_page(self):
        """다음 페이지"""
        max_p = (len(self.file_paths) - 1) // self.items_per_page if self.file_paths else 0
        if self.current_page < max_p:
            self.show_page(self.current_page + 1)


    def poll_usb(self):
        """USB 폴링 (타이머 콜백)"""
        self.detect_usb_devices()

    def detect_usb_devices(self):
        """USB 장치 감지"""
        current_devices = []
        
        # /media 디렉토리에서 마운트된 USB 찾기
        media_path = "/media"
        if os.path.exists(media_path):
            for user in os.listdir(media_path):
                user_path = os.path.join(media_path, user)
                if os.path.isdir(user_path):
                    for device in os.listdir(user_path):
                        device_path = os.path.join(user_path, device)
                        if os.path.isdir(device_path):
                            current_devices.append(device_path)

        # 변경 감지 시 목록 업데이트
        if current_devices != self.usb_devices:
            self.usb_devices = current_devices
            self.update_usb_file_list()

            if current_devices:
                self.usb_status_label.setText(f"USB 감지됨: {len(current_devices)}개 장치")
            else:
                self.usb_status_label.setText("USB 상태: 장치 없음")

# ======================= 파일 미리보기 및 프린팅 제어 클래스 =======================
class FilePreviewPage(QWidget):
    """선택된 파일 미리보기 및 프린팅 제어 페이지"""
    def __init__(self, return_to_print_callback, return_to_home_callback):
        super().__init__()
        self.return_to_print = return_to_print_callback
        self.return_to_home = return_to_home_callback

        # 프린팅 상태 관리 변수
        self.is_printing = False
        self.current_file_path = ""
        self.total_layers = 0
        self.current_layer = 0
        self.projector_window = None
        self.print_params = {}
        
        # 사용자 설정값
        self.blade_speed_value = "1500"  # 블레이드 속도
        self.leveling_cycles_value = "1"  # 평탄화 횟수 (기본값 1회)
        self.led_power_value = "440"  # LED 파워 (기본값 440, 범위 91~1023)

        self._build_ui()

    def _build_ui(self):
        """미리보기 페이지 UI 구성"""
        # 타이틀
        title = QLabel("Print Preview & Control")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Bold))

        # 미리보기 이미지 라벨
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(400, 300)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #EEEEEE; border: 1px solid #CCC;")

        # 파일명 표시 라벨
        self.filename_label = QLabel("선택된 파일 없음")
        self.filename_label.setAlignment(Qt.AlignCenter)
        self.filename_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.filename_label.setStyleSheet("color: #333; margin: 5px;")

        # 프린팅 정보 라벨들
        self.info_layout = QVBoxLayout()
        self.info_labels = {}
        
        info_items = [
            ("총 레이어", "totalLayer"),
            ("바닥 레이어 수", "bottomLayerCount"),
            ("바닥 노출시간", "bottomLayerExposureTime"),
            ("일반 노출시간", "normalExposureTime"),
            ("리프트 높이", "normalLayerLiftHeight"),
            ("리프트 속도", "normalLayerLiftSpeed")
        ]
        
        for display_name, key in info_items:
            label = QLabel(f"{display_name}: -")
            label.setStyleSheet("font-size: 11px; color: #666; margin: 2px;")
            self.info_labels[key] = label
            self.info_layout.addWidget(label)

        # 블레이드 속도 입력 필드 (버튼 방식으로 변경)
        blade_speed_layout = QHBoxLayout()
        blade_speed_label = QLabel("블레이드 속도:")
        blade_speed_label.setStyleSheet("font-size: 11px; color: #666; margin: 2px;")

        # QLineEdit 대신 QPushButton 사용
        self.blade_speed_button = QPushButton(self.blade_speed_value)
        self.blade_speed_button.setFixedWidth(100)
        self.blade_speed_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #5B9BD5;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
                text-align: left;
                color: #333;
            }
            QPushButton:pressed {
                background-color: #E3F2FD;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
        """)
        self.blade_speed_button.clicked.connect(self._open_blade_speed_keypad)

        blade_speed_unit = QLabel("mm/min")
        blade_speed_unit.setStyleSheet("font-size: 11px; color: #666; margin: 2px;")

        blade_speed_layout.addWidget(blade_speed_label)
        blade_speed_layout.addWidget(self.blade_speed_button)
        blade_speed_layout.addWidget(blade_speed_unit)
        blade_speed_layout.addStretch()

        self.info_layout.addLayout(blade_speed_layout)

        # 평탄화 횟수 입력 필드 (버튼 방식)
        leveling_layout = QHBoxLayout()
        leveling_label = QLabel("평탄화 횟수:")
        leveling_label.setStyleSheet("font-size: 11px; color: #666; margin: 2px;")

        self.leveling_cycles_button = QPushButton(self.leveling_cycles_value)
        self.leveling_cycles_button.setFixedWidth(100)
        self.leveling_cycles_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #5B9BD5;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
                text-align: left;
                color: #333;
            }
            QPushButton:pressed {
                background-color: #E3F2FD;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
        """)
        self.leveling_cycles_button.clicked.connect(self._open_leveling_cycles_keypad)

        leveling_unit = QLabel("회 (0~5)")
        leveling_unit.setStyleSheet("font-size: 11px; color: #666; margin: 2px;")

        leveling_layout.addWidget(leveling_label)
        leveling_layout.addWidget(self.leveling_cycles_button)
        leveling_layout.addWidget(leveling_unit)
        leveling_layout.addStretch()

        self.info_layout.addLayout(leveling_layout)

        # LED 파워 입력 필드 (버튼 방식)
        led_power_layout = QHBoxLayout()
        led_power_label = QLabel("LED 파워:")
        led_power_label.setStyleSheet("font-size: 11px; color: #666; margin: 2px;")

        self.led_power_button = QPushButton(self.led_power_value)
        self.led_power_button.setFixedWidth(100)
        self.led_power_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #5B9BD5;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
                text-align: left;
                color: #333;
            }
            QPushButton:pressed {
                background-color: #E3F2FD;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
        """)
        self.led_power_button.clicked.connect(self._open_led_power_keypad)

        led_power_unit = QLabel("(91~1023)")
        led_power_unit.setStyleSheet("font-size: 11px; color: #666; margin: 2px;")

        led_power_layout.addWidget(led_power_label)
        led_power_layout.addWidget(self.led_power_button)
        led_power_layout.addWidget(led_power_unit)
        led_power_layout.addStretch()

        self.info_layout.addLayout(led_power_layout)

        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(400, 25)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("진행률: %p% (0/0)")

        # 제어 버튼들
        self.btn_delete = QPushButton("파일 삭제")
        self.btn_start = QPushButton("프린팅 시작")
        self.btn_pause = QPushButton("일시정지")
        self.btn_stop = QPushButton("정지")
        self.btn_back = QPushButton("뒤로")

        # 버튼 스타일 및 크기 설정
        control_buttons = [self.btn_delete, self.btn_start, self.btn_pause, self.btn_back]
        for btn in control_buttons:
            btn.setFixedSize(120, 45)
            btn.setStyleSheet(BUTTON_STYLE)

        # 정지 버튼은 특별 스타일
        self.btn_stop.setFixedSize(120, 45)
        self.btn_stop.setStyleSheet(STOP_BUTTON_STYLE)

        # 초기 상태: 일시정지/정지 버튼 비활성화
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)

        # 이벤트 연결
        self.btn_delete.clicked.connect(self._delete_file)
        self.btn_start.clicked.connect(self._start_printing)
        self.btn_pause.clicked.connect(self._pause_printing)
        self.btn_stop.clicked.connect(self._stop_printing)
        self.btn_back.clicked.connect(self.return_to_print)

        # 레이아웃 구성
        # 좌측: 미리보기 + 파일명 + 프로그레스
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.preview_label)
        left_layout.addWidget(self.filename_label)
        left_layout.addWidget(self.progress_bar)

        # 우측: 정보 + 제어 버튼
        right_layout = QVBoxLayout()
        right_layout.addLayout(self.info_layout)
        right_layout.addWidget(self.btn_delete)
        right_layout.addWidget(self.btn_start)
        right_layout.addWidget(self.btn_pause)
        right_layout.addWidget(self.btn_stop)
        right_layout.addWidget(self.btn_back)

        # 메인 레이아웃
        content_layout = QHBoxLayout()
        content_layout.addLayout(left_layout)
        content_layout.addLayout(right_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(title)
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

    def update_progress(self, current_layer: int, total_layers: int):
        """프로그레스 바 업데이트"""
        self.current_layer = current_layer
        if total_layers > 0:
            progress_percent = int((current_layer / total_layers) * 100)
            self.progress_bar.setValue(progress_percent)
            self.progress_bar.setFormat(f"진행률: %p% ({current_layer}/{total_layers})")
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("진행률: %p% (0/0)")

    def show_file(self, file_path: str):
        """선택된 파일 표시 및 정보 추출"""
        self.current_file_path = file_path

        # 파일명 표시
        filename = os.path.basename(file_path)
        self.filename_label.setText(filename)

        # 파일 형식 확인
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".zip":
            # 프린팅 파라미터 추출
            self.print_params = extract_print_parameters(file_path)
            self.total_layers = self.print_params['totalLayer']
            
            # 정보 라벨 업데이트
            info_mapping = {
                'totalLayer': f"{self.print_params['totalLayer']}개",
                'bottomLayerCount': f"{self.print_params['bottomLayerCount']}개",
                'bottomLayerExposureTime': f"{self.print_params['bottomLayerExposureTime']}초",
                'normalExposureTime': f"{self.print_params['normalExposureTime']}초",
                'normalLayerLiftSpeed': f"{self.print_params.get('normalLayerLiftSpeed', 65)}mm/min"
            }
            
            for key, value in info_mapping.items():
                if key in self.info_labels:
                    display_name = {
                        'totalLayer': '총 레이어',
                        'bottomLayerCount': '바닥 레이어 수',
                        'bottomLayerExposureTime': '바닥 노출시간',
                        'normalExposureTime': '일반 노출시간',
                        'normalLayerLiftHeight': '리프트 높이',
                        'normalLayerLiftSpeed': '리프트 속도'
                    }[key]
                    self.info_labels[key].setText(f"{display_name}: {value}")
            
            print(f"추출된 프린팅 파라미터:")
            print(f"  - 총 레이어 수: {self.total_layers}")
            print(f"  - 바닥 레이어 수: {self.print_params['bottomLayerCount']}")
            print(f"  - 바닥 레이어 노출 시간: {self.print_params['bottomLayerExposureTime']}초")
            print(f"  - 일반 레이어 노출 시간: {self.print_params['normalExposureTime']}초")
            print(f"  - 리프트 높이: {self.print_params.get('normalLayerLiftHeight', 5.0)}mm")
            print(f"  - 리프트 속도: {self.print_params.get('normalLayerLiftSpeed', 65)}mm/min")

            # 미리보기 이미지 표시
            try:
                with zipfile.ZipFile(file_path, 'r') as z:
                    if "preview_cropping.png" in z.namelist():
                        data = z.read("preview_cropping.png")
                        pix = QPixmap()
                        pix.loadFromData(data)
                        self.preview_label.setPixmap(
                            pix.scaled(self.preview_label.size(), Qt.KeepAspectRatio)
                        )
                    else:
                        # preview_cropping.png가 없으면 기본 아이콘
                        fallback = QPixmap("/home/veri/GUI/icons/file.png")
                        self.preview_label.setPixmap(
                            fallback.scaled(self.preview_label.size(), Qt.KeepAspectRatio)
                        )
            except Exception as e:
                print(f"미리보기 이미지 로드 오류: {e}")
                fallback = QPixmap("/home/veri/GUI/icons/file.png")
                self.preview_label.setPixmap(
                    fallback.scaled(self.preview_label.size(), Qt.KeepAspectRatio)
                )
        else:
            # ZIP이 아닌 파일
            self.total_layers = 0
            self.print_params = {}
            
            # 정보 라벨 초기화
            for key, label in self.info_labels.items():
                display_name = {
                    'totalLayer': '총 레이어',
                    'bottomLayerCount': '바닥 레이어 수',
                    'bottomLayerExposureTime': '바닥 노출시간',
                    'normalExposureTime': '일반 노출시간',
                    'normalLayerLiftHeight': '리프트 높이',
                    'normalLayerLiftSpeed': '리프트 속도'
                }[key]
                label.setText(f"{display_name}: -")
            
            fallback = QPixmap("/home/veri/GUI/icons/file.png")
            self.preview_label.setPixmap(
                fallback.scaled(self.preview_label.size(), Qt.KeepAspectRatio)
            )

        # 프로그레스 바 초기화
        self.update_progress(0, self.total_layers)

    def _open_blade_speed_keypad(self):
        """블레이드 속도 입력 키패드 열기"""
        dialog = NumericKeypadDialog(
            parent=self,
            title="블레이드 속도 입력",
            default_value=self.blade_speed_value,
            unit="mm/min"
        )
        
        if dialog.exec() == QDialog.Accepted:
            # 입력된 값 저장 및 버튼 텍스트 업데이트
            self.blade_speed_value = dialog.get_value()
            self.blade_speed_button.setText(self.blade_speed_value)
            print(f"블레이드 속도 변경: {self.blade_speed_value} mm/min")

    def _open_leveling_cycles_keypad(self):
        """평탄화 횟수 입력 키패드 열기"""
        dialog = NumericKeypadDialog(
            parent=self,
            title="평탄화 횟수 입력 (0~5)",
            default_value=self.leveling_cycles_value,
            unit="회"
        )
        
        if dialog.exec() == QDialog.Accepted:
            # 입력된 값 검증 (0~5 범위)
            value_str = dialog.get_value()
            try:
                value = int(value_str)
                if 0 <= value <= 5:
                    self.leveling_cycles_value = str(value)
                    self.leveling_cycles_button.setText(self.leveling_cycles_value)
                    print(f"평탄화 횟수 변경: {self.leveling_cycles_value}회")
                else:
                    QMessageBox.warning(self, "입력 오류", "평탄화 횟수는 0~5 사이의 값이어야 합니다.")
            except ValueError:
                QMessageBox.warning(self, "입력 오류", "평탄화 횟수는 정수로 입력해주세요.")

    def _open_led_power_keypad(self):
        """LED 파워 입력 키패드 열기"""
        dialog = NumericKeypadDialog(
            parent=self,
            title="LED 파워 입력 (91~1023)",
            default_value=self.led_power_value,
            unit=""
        )

        if dialog.exec() == QDialog.Accepted:
            # 입력된 값 검증 (91~1023 범위)
            value_str = dialog.get_value()
            try:
                value = int(value_str)
                if 91 <= value <= 1023:
                    self.led_power_value = str(value)
                    self.led_power_button.setText(self.led_power_value)
                    print(f"LED 파워 변경: {self.led_power_value}")
                else:
                    QMessageBox.warning(self, "입력 오류", "LED 파워는 91~1023 사이의 값이어야 합니다.")
            except ValueError:
                QMessageBox.warning(self, "입력 오류", "LED 파워는 정수로 입력해주세요.")

    def _delete_file(self):
        """파일 삭제"""
        if not self.current_file_path:
            return
            
        reply = QMessageBox.question(
            self, 
            "파일 삭제", 
            f"'{os.path.basename(self.current_file_path)}'을(를) 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(self.current_file_path)
                QMessageBox.information(self, "삭제 완료", "파일이 삭제되었습니다.")
                self.return_to_print()
            except Exception as e:
                QMessageBox.critical(self, "삭제 실패", f"파일 삭제 중 오류가 발생했습니다:\n{str(e)}")

    def _start_printing(self):
        """프린팅 시작"""
        if not self.current_file_path or not self.print_params:
            QMessageBox.warning(self, "오류", "유효한 프린트 파일을 선택해주세요.")
            return

        # 블레이드 속도 입력값 검증
        try:
            blade_speed = float(self.blade_speed_value)
            if blade_speed <= 0:
                QMessageBox.warning(self, "입력 오류", "블레이드 속도는 0보다 커야 합니다.")
                return
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "블레이드 속도는 숫자로 입력해주세요.")
            return

        # 평탄화 횟수 입력값 검증
        try:
            leveling_cycles = int(self.leveling_cycles_value)
            if not (0 <= leveling_cycles <= 5):
                QMessageBox.warning(self, "입력 오류", "평탄화 횟수는 0~5 사이의 값이어야 합니다.")
                return
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "평탄화 횟수는 정수로 입력해주세요.")
            return

        # LED 파워 입력값 검증
        try:
            led_power = int(self.led_power_value)
            if not (91 <= led_power <= 1023):
                QMessageBox.warning(self, "입력 오류", "LED 파워는 91~1023 사이의 값이어야 합니다.")
                return
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "LED 파워는 정수로 입력해주세요.")
            return

        # 프린팅 상태 변경
        self.is_printing = True

        # 버튼 상태 변경
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_delete.setEnabled(False)
        self.btn_back.setEnabled(False)

        print(f"프린팅 시작: {self.current_file_path}")
        print(f"블레이드 속도: {blade_speed} mm/min")
        print(f"평탄화 횟수: {leveling_cycles}회")
        print(f"LED 파워: {led_power}")

        # DLP 슬라이드쇼 실행 (모터 제어 포함)
        try:
            self.projector_window = run_slideshow(
                self.current_file_path,
                progress_callback=self.update_progress,
                motor_callback=self._send_motor_command,
                blade_speed=blade_speed,  # 블레이드 속도 전달
                leveling_cycles=leveling_cycles,  # 평탄화 횟수 전달
                led_power=led_power  # LED 파워 전달
            )
        except Exception as e:
            print(f"프린팅 시작 오류: {e}")
            self._reset_buttons()
            QMessageBox.critical(self, "프린팅 오류", f"프린팅 시작 중 오류가 발생했습니다:\n{str(e)}")

    def _pause_printing(self):
        """프린팅 일시정지/재개"""
        if self.projector_window and hasattr(self.projector_window, 'pause_func') and self.projector_window.pause_func:
            if self.btn_pause.text() == "일시정지":
                print("일시정지 버튼 클릭")
                self.projector_window.pause_func()
                self.btn_pause.setText("재개")
                print("프린팅 일시정지 완료")
            else:
                print("재개 버튼 클릭")
                self.projector_window.resume_func()
                self.btn_pause.setText("일시정지")
                print("프린팅 재개 완료")
        else:
            print("일시정지/재개 기능을 사용할 수 없습니다.")

    def _stop_printing(self):
        """프린팅 정지"""
        print("정지 버튼 클릭")

        # 정지 확인 대화상자
        dialog = StopConfirmationDialog(self)
        result = dialog.exec()
        print(f"정지 확인 대화상자 결과: {result}")

        if result == QDialog.Accepted:
            print("사용자가 정지 확인함")

            # 프로젝터 윈도우 정지
            if self.projector_window and hasattr(self.projector_window, 'stop_func') and self.projector_window.stop_func:
                print("stop_func 호출")
                self.projector_window.stop_func()
                print("정지 요청 완료")
            else:
                print("stop_func를 사용할 수 없습니다.")

            # 상태 초기화
            self.is_printing = False
            self._reset_buttons()

            # 프로그레스 바 초기화
            self.update_progress(0, self.total_layers)
            print("프린팅 정지 처리 완료")
        else:
            print("사용자가 정지 취소함")

    def _reset_buttons(self):
        """버튼 상태 초기화"""
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("일시정지")
        self.btn_stop.setEnabled(False)
        self.btn_delete.setEnabled(True)
        self.btn_back.setEnabled(True)

    def _send_motor_command(self, gcode_command):
        """모터 제어 명령 전송"""
        try:
            url = f"{MOONRAKER_URL}/printer/gcode/script"
            data = {"script": gcode_command}
            response = requests.post(url, json=data, timeout=200)
            
            if response.status_code == 200:
                print(f"모터 명령 전송 성공: {gcode_command}")
                return True
            else:
                print(f"모터 명령 전송 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"모터 제어 오류: {e}")
            return False

# ======================= 메인 윈도우 클래스 =======================
class MainWindow(QMainWindow):
    """메인 윈도우"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DLP 3D 프린터 제어 시스템 v2.0")
        self.setFixedSize(800, 480)  # 7인치 LCD에 최적화

        # 스택 위젯으로 페이지 관리
        self.stack = QStackedWidget()
        
        # 페이지들 생성
        self.home_page = HomeMenu(self.show_tools_page)
        self.tools_page = ToolsMenu(self.show_home_page)
        self.movez_page = MoveZMenu(self.show_tools_page)
        self.print_page = PrintMenu(self.show_home_page)
        self.preview_page = FilePreviewPage(self.show_print_page, self.show_home_page)

        # 스택에 페이지 추가
        for page in [self.home_page, self.tools_page, self.movez_page, self.print_page, self.preview_page]:
            self.stack.addWidget(page)

        self.setCentralWidget(self.stack)

        # 홈 페이지의 Print 버튼 연결
        for btn in self.home_page.findChildren(QPushButton):
            if btn.text() == "Print":
                btn.clicked.connect(self.show_print_page)
                break

        # 도구 페이지의 Move Z 버튼 연결
        for btn in self.tools_page.findChildren(QPushButton):
            if btn.text() == "Move Z":
                btn.clicked.connect(self.show_movez_page)
                break

        # 프린트 페이지의 Enter 버튼 연결
        self.print_page.btn_enter.clicked.connect(self.show_preview_page)

    def show_home_page(self):
        """홈 페이지 표시"""
        self.stack.setCurrentWidget(self.home_page)
        self.print_page.stop_polling()

    def show_tools_page(self):
        """도구 페이지 표시"""
        self.stack.setCurrentWidget(self.tools_page)
        self.print_page.stop_polling()

    def show_movez_page(self):
        """Z축 이동 페이지 표시"""
        self.stack.setCurrentWidget(self.movez_page)
        self.print_page.stop_polling()

    def show_print_page(self):
        """프린트 페이지 표시"""
        self.stack.setCurrentWidget(self.print_page)
        self.print_page.start_polling()

    def show_preview_page(self):
        """미리보기 페이지 표시"""
        idx = self.print_page.selected_button_index
        if idx is None:
            QMessageBox.warning(self, "선택 오류", "프린트 파일을 선택해주세요.")
            return
            
        # 선택된 파일이 유효한지 확인
        if idx < len(self.print_page.file_paths):
            file_path = self.print_page.file_paths[idx]
            self.preview_page.show_file(file_path)
            self.stack.setCurrentWidget(self.preview_page)
            self.print_page.stop_polling()
        else:
            QMessageBox.warning(self, "파일 오류", "유효하지 않은 파일입니다.")

    def closeEvent(self, event):
        """애플리케이션 종료 시 정리"""
        print("DLP 프린터 제어 시스템 종료")
        
        # 프린팅 중이면 정지
        if hasattr(self.preview_page, 'is_printing') and self.preview_page.is_printing:
            if self.preview_page.projector_window and hasattr(self.preview_page.projector_window, 'stop_func'):
                self.preview_page.projector_window.stop_func()
        
        # USB 폴링 중지
        self.print_page.stop_polling()
        
        event.accept()

# ======================= 메인 실행 =======================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 애플리케이션 스타일 설정
    app.setStyleSheet("""
        QMainWindow {
            background-color: #F5F5F5;
        }
        QWidget {
            font-family: Arial, sans-serif;
        }
        QLabel {
            color: #333333;
        }
        QProgressBar {
            border: 2px solid #C0C0C0;
            border-radius: 5px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 3px;
        }
    """)
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    print("DLP 3D 프린터 제어 시스템이 시작되었습니다.")
    
    # 애플리케이션 실행
    sys.exit(app.exec())