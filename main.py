#!/usr/bin/env python3
"""
VERICOM DLP 3D Printer GUI System
메인 진입점 및 윈도우 관리

Version: 2.1
Design: Navy + Cyan Theme
Resolution: 1024x600 (7inch Touch LCD)
Mode: Kiosk/Fullscreen
"""

import sys
import os

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCursor

from styles.stylesheets import GLOBAL_STYLE
from pages.main_page import MainPage
from pages.tool_page import ToolPage
from pages.manual_page import ManualPage
from pages.print_page import PrintPage
from pages.exposure_page import ExposurePage
from pages.clean_page import CleanPage
from pages.system_page import SystemPage
from pages.device_info_page import DeviceInfoPage
from pages.language_page import LanguagePage
from pages.service_page import ServicePage
from pages.file_preview_page import FilePreviewPage
from pages.print_progress_page import PrintProgressPage

# 하드웨어 컨트롤러
from controllers.motor_controller import MotorController
from controllers.dlp_controller import DLPController
from controllers.gcode_parser import extract_print_parameters

# 워커
from workers.print_worker import PrintWorker, PrintStatus

# 프로젝터 윈도우
from windows.projector_window import ProjectorWindow

# 화면 설정
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
KIOSK_MODE = False  # 개발 중에는 False, 실제 배포 시 True

# Moonraker 설정
MOONRAKER_URL = "http://localhost:7125"

# 시뮬레이션 모드 (하드웨어 없이 테스트)
SIMULATION_MODE = False  # 실제 하드웨어 사용


class MainWindow(QMainWindow):
    """메인 윈도우 - 키오스크 모드 지원"""

    # 페이지 인덱스
    PAGE_MAIN = 0
    PAGE_TOOL = 1
    PAGE_MANUAL = 2
    PAGE_PRINT = 3
    PAGE_EXPOSURE = 4
    PAGE_CLEAN = 5
    PAGE_SYSTEM = 6
    PAGE_DEVICE_INFO = 7
    PAGE_LANGUAGE = 8
    PAGE_SERVICE = 9
    PAGE_FILE_PREVIEW = 10
    PAGE_PRINT_PROGRESS = 11

    def __init__(self, kiosk_mode: bool = False, simulation: bool = True):
        super().__init__()

        self.setWindowTitle("VERICOM DLP 3D Printer v2.1")
        self.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)

        # 키오스크 모드 설정
        if kiosk_mode:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setCursor(Qt.BlankCursor)  # 터치 전용이므로 커서 숨김

        # 시뮬레이션 모드
        self.simulation = simulation

        # 하드웨어 컨트롤러 초기화
        self._init_hardware()

        # 페이지 설정
        self._setup_pages()
        self._connect_signals()

        # 프린트 워커
        self.print_worker = None

        # 프로젝터 윈도우 (두 번째 모니터)
        self.projector_window = None

    def _init_hardware(self):
        """하드웨어 컨트롤러 초기화"""
        # 모터 컨트롤러
        self.motor = MotorController(MOONRAKER_URL)
        if not self.simulation:
            self.motor.connect()

        # DLP 컨트롤러
        self.dlp = DLPController(simulation=self.simulation)
        self.dlp.initialize()

        print(f"[System] 하드웨어 초기화 완료 (시뮬레이션: {self.simulation})")
    
    def _setup_pages(self):
        """페이지 설정"""
        self.stack = QStackedWidget()
        
        # 페이지 생성
        self.main_page = MainPage()
        self.tool_page = ToolPage()
        self.manual_page = ManualPage()
        self.print_page = PrintPage()
        self.exposure_page = ExposurePage()
        self.clean_page = CleanPage()
        self.system_page = SystemPage()
        self.device_info_page = DeviceInfoPage()
        self.language_page = LanguagePage()
        self.service_page = ServicePage()
        self.file_preview_page = FilePreviewPage()
        self.print_progress_page = PrintProgressPage()
        
        # 스택에 추가
        self.stack.addWidget(self.main_page)         # 0
        self.stack.addWidget(self.tool_page)         # 1
        self.stack.addWidget(self.manual_page)       # 2
        self.stack.addWidget(self.print_page)        # 3
        self.stack.addWidget(self.exposure_page)     # 4
        self.stack.addWidget(self.clean_page)        # 5
        self.stack.addWidget(self.system_page)       # 6
        self.stack.addWidget(self.device_info_page)  # 7
        self.stack.addWidget(self.language_page)     # 8
        self.stack.addWidget(self.service_page)      # 9
        self.stack.addWidget(self.file_preview_page) # 10
        self.stack.addWidget(self.print_progress_page) # 11
        
        self.setCentralWidget(self.stack)
    
    def _connect_signals(self):
        """시그널 연결"""
        # 메인 페이지
        self.main_page.go_tool.connect(lambda: self._go_to_page(self.PAGE_TOOL))
        self.main_page.go_print.connect(lambda: self._go_to_page(self.PAGE_PRINT))
        self.main_page.go_system.connect(lambda: self._go_to_page(self.PAGE_SYSTEM))
        
        # 도구 페이지
        self.tool_page.go_back.connect(lambda: self._go_to_page(self.PAGE_MAIN))
        self.tool_page.go_manual.connect(lambda: self._go_to_page(self.PAGE_MANUAL))
        self.tool_page.go_exposure.connect(lambda: self._go_to_page(self.PAGE_EXPOSURE))
        self.tool_page.go_clean.connect(lambda: self._go_to_page(self.PAGE_CLEAN))
        self.tool_page.stop_all.connect(self._emergency_stop)
        
        # 매뉴얼 페이지
        self.manual_page.go_back.connect(lambda: self._go_to_page(self.PAGE_TOOL))
        self.manual_page.z_move.connect(self._move_z)
        self.manual_page.z_home.connect(self._home_z)
        self.manual_page.x_move.connect(self._move_x)
        self.manual_page.x_home.connect(self._home_x)
        
        # 프린트 페이지
        self.print_page.go_back.connect(lambda: self._go_to_page(self.PAGE_MAIN))
        self.print_page.file_selected.connect(self._on_file_selected)
        
        # 노출 테스트 페이지
        self.exposure_page.go_back.connect(lambda: self._go_to_page(self.PAGE_TOOL))
        self.exposure_page.exposure_start.connect(self._start_exposure)
        self.exposure_page.exposure_stop.connect(self._stop_exposure)
        
        # 클리닝 페이지
        self.clean_page.go_back.connect(lambda: self._go_to_page(self.PAGE_TOOL))
        self.clean_page.clean_start.connect(self._start_clean)
        self.clean_page.clean_stop.connect(self._stop_clean)
        
        # 시스템 페이지
        self.system_page.go_back.connect(lambda: self._go_to_page(self.PAGE_MAIN))
        self.system_page.go_device_info.connect(lambda: self._go_to_page(self.PAGE_DEVICE_INFO))
        self.system_page.go_language.connect(lambda: self._go_to_page(self.PAGE_LANGUAGE))
        self.system_page.go_service.connect(lambda: self._go_to_page(self.PAGE_SERVICE))
        
        # 장치 정보 페이지
        self.device_info_page.go_back.connect(lambda: self._go_to_page(self.PAGE_SYSTEM))
        
        # 언어 설정 페이지
        self.language_page.go_back.connect(lambda: self._go_to_page(self.PAGE_SYSTEM))
        self.language_page.language_changed.connect(self._on_language_changed)
        
        # 서비스 정보 페이지
        self.service_page.go_back.connect(lambda: self._go_to_page(self.PAGE_SYSTEM))
        
        # 파일 미리보기 페이지
        self.file_preview_page.go_back.connect(lambda: self._go_to_page(self.PAGE_PRINT))
        self.file_preview_page.start_print.connect(self._on_start_print)
        self.file_preview_page.file_deleted.connect(self._on_file_deleted)
        
        # 프린트 진행 페이지
        self.print_progress_page.go_home.connect(lambda: self._go_to_page(self.PAGE_MAIN))
        self.print_progress_page.pause_requested.connect(self._on_print_pause)
        self.print_progress_page.resume_requested.connect(self._on_print_resume)
        self.print_progress_page.stop_requested.connect(self._on_print_stop)
    
    def _go_to_page(self, page_index: int):
        """페이지 전환"""
        self.stack.setCurrentIndex(page_index)
    
    # ==================== 하드웨어 제어 ====================

    def _move_z(self, distance: float):
        """Z축 이동"""
        print(f"[Motor] Z축 이동: {distance}mm")
        self.motor.z_move_relative(distance)

    def _home_z(self):
        """Z축 홈"""
        print("[Motor] Z축 홈으로 이동")
        self.motor.z_home()

    def _move_x(self, distance: float):
        """X축(블레이드) 이동"""
        print(f"[Motor] X축 이동: {distance}mm")
        self.motor.x_move_relative(distance)

    def _home_x(self):
        """X축 홈"""
        print("[Motor] X축 홈으로 이동")
        self.motor.x_home()

    def _emergency_stop(self):
        """비상 정지"""
        print("[EMERGENCY] 모든 동작 정지!")
        # 모터 비상 정지
        self.motor.emergency_stop()
        # LED 끄기
        self.dlp.led_off()
        self.dlp.projector_off()
        # 프린트 워커 정지
        if self.print_worker and self.print_worker.isRunning():
            self.print_worker.stop()
    
    def _on_file_selected(self, file_path: str):
        """파일 선택됨 -> File Preview로 이동"""
        print(f"[Print] 파일 선택: {file_path}")
        self.file_preview_page.set_file(file_path)
        self._go_to_page(self.PAGE_FILE_PREVIEW)
    
    def _on_start_print(self, file_path: str, params: dict):
        """프린트 시작"""
        print(f"[Print] 프린트 시작: {file_path}")
        print(f"  - 파라미터: {params}")

        # 썸네일 가져오기
        thumbnail = None
        if hasattr(self.file_preview_page, 'lbl_thumbnail'):
            pixmap = self.file_preview_page.lbl_thumbnail.pixmap()
            if pixmap:
                thumbnail = pixmap

        # 파라미터 추출
        total_layers = params.get('totalLayer', 100)
        blade_speed = params.get('bladeSpeed', 1500)
        led_power_percent = params.get('ledPower', 100)  # 퍼센트 (100% = 440)
        led_power = int(440 * led_power_percent / 100)   # 실제 LED 값으로 변환
        leveling_cycles = params.get('levelingCycles', 1)

        # Print Progress 페이지로 정보 전달 및 이동
        self.print_progress_page.set_print_info(
            file_path=file_path,
            thumbnail=thumbnail,
            total_layers=total_layers,
            blade_speed=blade_speed,
            led_power=led_power
        )
        self._go_to_page(self.PAGE_PRINT_PROGRESS)

        # 프로젝터 윈도우 생성 및 표시
        if self.projector_window is None:
            self.projector_window = ProjectorWindow(screen_index=1)
        screens = QApplication.screens()
        if len(screens) > 1:
            self.projector_window.show_on_screen(1)
        else:
            print("[Projector] 두 번째 모니터 없음, 프로젝터 윈도우 생략")

        # PrintWorker 생성 및 시작
        self.print_worker = PrintWorker(
            motor=self.motor,
            dlp=self.dlp,
            parent=self
        )
        self.print_worker.simulation = self.simulation

        # 워커 시그널 연결
        self.print_worker.progress_updated.connect(self._on_progress_updated)
        self.print_worker.print_completed.connect(self._on_print_completed)
        self.print_worker.print_stopped.connect(self._on_print_stopped_by_worker)
        self.print_worker.error_occurred.connect(self._on_print_error)

        # 프로젝터 윈도우에 이미지 표시 연결
        if self.projector_window:
            self.print_worker.show_image.connect(self.projector_window.show_image)
            self.print_worker.clear_image.connect(self.projector_window.clear_screen)

        # 프린트 시작
        self.print_worker.start_print(
            file_path=file_path,
            params=params,
            blade_speed=blade_speed,
            led_power=led_power,
            leveling_cycles=leveling_cycles
        )

    def _on_progress_updated(self, current: int, total: int):
        """프린트 진행률 업데이트"""
        self.print_progress_page.update_progress(current, total)

    def _on_print_completed(self):
        """프린트 완료"""
        print("[Print] 프린트 완료!")
        if self.projector_window:
            self.projector_window.close()
        self.print_progress_page.show_completed()

    def _on_print_stopped_by_worker(self):
        """워커에 의한 프린트 정지"""
        print("[Print] 프린트 정지됨")
        if self.projector_window:
            self.projector_window.close()
        self.print_progress_page.show_stopped()

    def _on_print_error(self, message: str):
        """프린트 오류"""
        print(f"[Print] 오류: {message}")
        if self.projector_window:
            self.projector_window.close()

    def _on_print_pause(self):
        """프린트 일시정지"""
        print("[Print] 일시정지 요청")
        if self.print_worker and self.print_worker.isRunning():
            self.print_worker.pause()

    def _on_print_resume(self):
        """프린트 재개"""
        print("[Print] 재개 요청")
        if self.print_worker and self.print_worker.isRunning():
            self.print_worker.resume()

    def _on_print_stop(self):
        """프린트 정지"""
        print("[Print] 정지 요청")
        if self.print_worker and self.print_worker.isRunning():
            self.print_worker.stop()
        else:
            self.print_progress_page.show_stopped()
    
    def _on_file_deleted(self, file_path: str):
        """파일 삭제됨"""
        print(f"[Print] 파일 삭제됨: {file_path}")
    
    def _start_exposure(self, pattern: str, time: float):
        """노출 테스트 시작"""
        pattern_value = self.exposure_page.get_pattern_value()

        print(f"[NVR] 노출 테스트 시작")
        print(f"  - 패턴: {pattern} (0x{pattern_value:02X})")
        print(f"  - 시간: {time}초")

        # 프로젝터 윈도우에 패턴 표시
        if self.projector_window is None:
            self.projector_window = ProjectorWindow(screen_index=1)

        screens = QApplication.screens()
        if len(screens) > 1:
            self.projector_window.show_on_screen(1)
            self.projector_window.show_test_pattern(pattern)

        # 프로젝터 ON + LED ON
        self.dlp.projector_on()
        self.dlp.led_on(440)

    def _stop_exposure(self):
        """노출 테스트 정지"""
        print("[NVR] 노출 테스트 정지")
        self.dlp.led_off()
        self.dlp.projector_off()

        if self.projector_window:
            self.projector_window.clear_screen()
            self.projector_window.close()

    def _start_clean(self, time: float):
        """클리닝 시작"""
        print(f"[NVR] 클리닝 시작")
        print(f"  - 시간: {time}초")

        # 1. 프로젝터 윈도우에 흰색 화면 표시
        if self.projector_window is None:
            self.projector_window = ProjectorWindow(screen_index=1)

        screens = QApplication.screens()
        if len(screens) > 1:
            self.projector_window.show_on_screen(1)
            self.projector_window.show_white_screen()

        # 2. 프로젝터 ON
        self.dlp.projector_on()

        # 3. LED 파워 440 설정 + LED ON
        print(f"  - LED Power: 440")
        self.dlp.led_on(440)

    def _stop_clean(self):
        """클리닝 정지"""
        print("[NVR] 클리닝 정지")
        self.dlp.led_off()
        self.dlp.projector_off()

        if self.projector_window:
            self.projector_window.clear_screen()
            self.projector_window.close()
    
    # ==================== 시스템 메뉴 ====================
    
    def _on_language_changed(self, lang_code: str):
        """언어 변경됨"""
        print(f"[System] Language changed to: {lang_code}")
        # TODO: 언어 설정 저장 및 적용
    
    def _send_gcode(self, gcode: str):
        """G-code 전송 (Moonraker API)"""
        # TODO: Moonraker API 연동
        pass
    
    def closeEvent(self, event):
        """앱 종료 시"""
        print("[System] VERICOM DLP Printer GUI 종료")

        # 프린트 워커 정지
        if self.print_worker and self.print_worker.isRunning():
            self.print_worker.stop()
            self.print_worker.wait(3000)  # 최대 3초 대기

        # 프로젝터 윈도우 닫기
        if self.projector_window:
            self.projector_window.close()

        # 하드웨어 정리
        if not self.simulation:
            self.dlp.led_off()
            self.dlp.projector_off()

        event.accept()


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='VERICOM DLP 3D Printer GUI')
    parser.add_argument('--kiosk', action='store_true', help='키오스크 모드로 실행')
    parser.add_argument('--windowed', action='store_true', help='윈도우 모드로 실행 (개발용)')
    parser.add_argument('--no-sim', action='store_true', help='실제 하드웨어 모드 (시뮬레이션 비활성화)')
    parser.add_argument('--sim', action='store_true', help='시뮬레이션 모드 (기본값)')
    args = parser.parse_args()

    # 키오스크 모드 결정 (기본값: KIOSK_MODE 상수)
    kiosk = KIOSK_MODE
    if args.windowed:
        kiosk = False
    elif args.kiosk:
        kiosk = True

    # 시뮬레이션 모드 결정 (기본값: SIMULATION_MODE 상수)
    simulation = SIMULATION_MODE
    if args.no_sim:
        simulation = False
    elif args.sim:
        simulation = True

    print("=" * 50)
    print("VERICOM DLP 3D Printer GUI v2.1")
    print(f"Resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"Mode: {'Kiosk' if kiosk else 'Windowed'}")
    print(f"Hardware: {'Simulation' if simulation else 'Real'}")
    print("=" * 50)

    app = QApplication(sys.argv)

    # 글로벌 스타일 적용
    app.setStyleSheet(GLOBAL_STYLE)

    # 메인 윈도우 생성 및 표시
    window = MainWindow(kiosk_mode=kiosk, simulation=simulation)

    if kiosk:
        window.showFullScreen()
    else:
        window.show()

    print("[System] GUI 시작됨")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
