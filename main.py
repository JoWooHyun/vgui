#!/usr/bin/env python3
"""
VERICOM DLP 3D Printer GUI System
메인 진입점 및 윈도우 관리

Version: 2.0
Design: Navy + Cyan Theme
"""

import sys
import os

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt

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


class MainWindow(QMainWindow):
    """메인 윈도우"""
    
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
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("VERICOM DLP 3D Printer v2.0")
        self.setFixedSize(800, 480)
        
        # 풀스크린 모드 (라즈베리파이용)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        
        self._setup_pages()
        self._connect_signals()
    
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
        # TODO: 실제 모터 제어 구현
        # self._send_gcode(f"G91\nG1 Z{distance} F300\nG90")
    
    def _home_z(self):
        """Z축 홈"""
        print("[Motor] Z축 홈으로 이동")
        # TODO: 실제 모터 제어 구현
        # self._send_gcode("G28 Z")
    
    def _move_x(self, distance: float):
        """X축(블레이드) 이동"""
        print(f"[Motor] X축 이동: {distance}mm")
        # TODO: 실제 모터 제어 구현
    
    def _home_x(self):
        """X축 홈"""
        print("[Motor] X축 홈으로 이동")
        # TODO: 실제 모터 제어 구현
    
    def _emergency_stop(self):
        """비상 정지"""
        print("[EMERGENCY] 모든 동작 정지!")
        # TODO: 모든 모터/LED 정지
    
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
        
        # 총 레이어 수 (파라미터에서 또는 기본값)
        total_layers = params.get('totalLayer', 100)
        blade_speed = params.get('bladeSpeed', 1500)
        led_power = params.get('ledPower', 100)
        
        # Print Progress 페이지로 정보 전달 및 이동
        self.print_progress_page.set_print_info(
            file_path=file_path,
            thumbnail=thumbnail,
            total_layers=total_layers,
            blade_speed=blade_speed,
            led_power=led_power
        )
        self._go_to_page(self.PAGE_PRINT_PROGRESS)
        
        # TODO: PrintWorker 스레드 시작
    
    def _on_print_pause(self):
        """프린트 일시정지"""
        print("[Print] 일시정지 요청")
        # TODO: Worker에 일시정지 신호
    
    def _on_print_resume(self):
        """프린트 재개"""
        print("[Print] 재개 요청")
        # TODO: Worker에 재개 신호
    
    def _on_print_stop(self):
        """프린트 정지"""
        print("[Print] 정지 요청")
        # TODO: Worker 정지 및 정리
        self.print_progress_page.show_stopped()
    
    def _on_file_deleted(self, file_path: str):
        """파일 삭제됨"""
        print(f"[Print] 파일 삭제됨: {file_path}")
    
    def _start_exposure(self, pattern: str, h_flip: bool, v_flip: bool, time: float):
        """노출 테스트 시작"""
        flip_value = self.exposure_page.get_flip_value()
        pattern_value = self.exposure_page.get_pattern_value()
        
        print(f"[NVR] 노출 테스트 시작")
        print(f"  - 패턴: {pattern} (0x{pattern_value:02X})")
        print(f"  - 반전: H={h_flip}, V={v_flip} (0x{flip_value:02X})")
        print(f"  - 시간: {time}초")
        
        # TODO: NVR2+ 제어 구현
        # 1. 패턴 설정 (Command 0x05, 0x0b)
        # 2. 반전 설정 (Command 0x14)
        # 3. LED 켜기 (Command 0x07)
    
    def _stop_exposure(self):
        """노출 테스트 정지"""
        print("[NVR] 노출 테스트 정지")
        # TODO: LED 끄기 (Command 0x00)
    
    def _start_clean(self, time: float):
        """클리닝 시작"""
        print(f"[NVR] 클리닝 시작")
        print(f"  - 시간: {time}초")
        # TODO: 전체 화면 흰색 + LED 켜기
    
    def _stop_clean(self):
        """클리닝 정지"""
        print("[NVR] 클리닝 정지")
        # TODO: LED 끄기
    
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
        # TODO: 정리 작업
        event.accept()


def main():
    """메인 함수"""
    print("=" * 50)
    print("VERICOM DLP 3D Printer GUI v2.0")
    print("Design: Navy + Cyan Theme")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    # 글로벌 스타일 적용
    app.setStyleSheet(GLOBAL_STYLE)
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    print("[System] GUI 시작됨")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
