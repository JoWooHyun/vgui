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

# 테마 매니저를 가장 먼저 초기화 (Colors에 저장된 테마 적용)
# 이후 임포트되는 모듈들이 올바른 테마 색상을 사용하도록 함
from controllers.theme_manager import get_theme_manager
_theme_init = get_theme_manager()  # 테마 로드 및 Colors 적용

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QMessageBox, QDialog,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject
from PySide6.QtGui import QCursor


class MotorWorker(QObject):
    """모터 작업을 백그라운드에서 실행하는 워커"""
    finished = Signal()
    error = Signal(str)

    def __init__(self, motor, operation: str, **kwargs):
        super().__init__()
        self.motor = motor
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        """모터 작업 실행"""
        try:
            if self.operation == "z_move":
                distance = self.kwargs.get("distance", 0)
                self.motor.z_move_relative(distance)
            elif self.operation == "z_home":
                self.motor.z_home()
            elif self.operation == "x_move":
                distance = self.kwargs.get("distance", 0)
                speed = self.kwargs.get("speed", 300)
                self.motor.x_move_relative(distance, speed=speed)
            elif self.operation == "x_home":
                self.motor.x_home()
            elif self.operation == "y_move":
                distance = self.kwargs.get("distance", 0)
                self.motor.y_move_relative(distance)
            elif self.operation == "y_home":
                self.motor.y_home()
            elif self.operation == "y_reset_position":
                self.motor.y_reset_position()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import get_global_style
from pages.main_page import MainPage
from pages.tool_page import ToolPage, SimpleAlert
from pages.manual_page import ManualPage
from pages.print_page import PrintPage
from pages.exposure_page import ExposurePage
from pages.leveling_page import LevelingPage
from pages.system_page import SystemPage
from pages.device_info_page import DeviceInfoPage
from pages.language_page import LanguagePage
from pages.service_page import ServicePage
from pages.file_preview_page import FilePreviewPage, ZipErrorDialog
from pages.print_progress_page import PrintProgressPage, ErrorDialog
from pages.setting_page import SettingPage
from pages.theme_page import ThemePage
from pages.material_page import MaterialPage

# 하드웨어 컨트롤러
from controllers.motor_controller import MotorController
from controllers.dlp_controller import DLPController
from controllers.gcode_parser import extract_print_parameters, validate_zip_file
from controllers.settings_manager import get_settings
# theme_manager는 이미 상단에서 임포트됨

# 워커
from workers.print_worker import PrintWorker, PrintStatus

# 프로젝터 윈도우
from windows.projector_window import ProjectorWindow

# 키오스크 관리자
from utils.kiosk_manager import get_kiosk_manager

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
    PAGE_SYSTEM = 5
    PAGE_DEVICE_INFO = 6
    PAGE_LANGUAGE = 7
    PAGE_SERVICE = 8
    PAGE_FILE_PREVIEW = 9
    PAGE_PRINT_PROGRESS = 10
    PAGE_SETTING = 11
    PAGE_THEME = 12
    PAGE_LEVELING = 13
    PAGE_MATERIAL = 14

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

        # 설정 관리자
        self.settings = get_settings()

        # 테마 관리자 (Colors 클래스에 저장된 테마 적용)
        self.theme_manager = get_theme_manager()

        # 페이지 설정
        self._setup_pages()
        self._connect_signals()

        # 저장된 설정 적용
        self._apply_saved_settings()

        # 테마 변경 시그널 연결
        self.theme_manager.theme_changed.connect(self._on_theme_changed)

        # 프린트 워커
        self.print_worker = None

        # 모터 워커 (비동기 모터 제어용)
        self._motor_threads = []

        # 프로젝터 윈도우 (두 번째 모니터)
        self.projector_window = None

        # 키오스크 관리자 설정
        self.kiosk_manager = get_kiosk_manager()
        self.kiosk_manager.set_enabled(kiosk_mode)
        self.kiosk_manager.admin_mode_changed.connect(self._on_admin_mode_changed)

        # 이벤트 필터 설치 (키오스크 모드일 때만)
        if kiosk_mode:
            QApplication.instance().installEventFilter(self.kiosk_manager)

    def _init_hardware(self):
        """하드웨어 컨트롤러 초기화"""
        # 모터 컨트롤러
        self.motor = MotorController(MOONRAKER_URL)
        if not self.simulation:
            self.motor.connect()

        # DLP 컨트롤러
        self.dlp = DLPController(simulation=self.simulation)
        dlp_success = self.dlp.initialize()

        # DLP 초기화 성공 시 프로젝터 ON (앱 실행 동안 계속 켜둠)
        if dlp_success:
            self.dlp.projector_on()
            print("[System] 프로젝터 ON (앱 시작)")
        else:
            # 초기화 실패 시 경고 팝업 (QTimer로 지연 - UI 초기화 후 표시)
            QTimer.singleShot(500, self._show_dlp_error_popup)

        print(f"[System] 하드웨어 초기화 완료 (시뮬레이션: {self.simulation})")

    def _show_dlp_error_popup(self):
        """DLP 연결 실패 경고 팝업"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("프로젝터 연결 실패")
        msg.setText("프로젝터 연결에 실패했습니다.\n\n전원을 껐다가 다시 켜주세요.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
    
    def _setup_pages(self):
        """페이지 설정"""
        self.stack = QStackedWidget()
        
        # 페이지 생성
        self.main_page = MainPage()
        self.tool_page = ToolPage()
        self.manual_page = ManualPage()
        self.print_page = PrintPage()
        self.exposure_page = ExposurePage()
        self.system_page = SystemPage()
        self.device_info_page = DeviceInfoPage()
        self.language_page = LanguagePage()
        self.service_page = ServicePage()
        self.file_preview_page = FilePreviewPage()
        self.print_progress_page = PrintProgressPage()
        self.setting_page = SettingPage()
        self.theme_page = ThemePage()
        self.leveling_page = LevelingPage()
        self.material_page = MaterialPage()

        # 스택에 추가
        self.stack.addWidget(self.main_page)         # 0
        self.stack.addWidget(self.tool_page)         # 1
        self.stack.addWidget(self.manual_page)       # 2
        self.stack.addWidget(self.print_page)        # 3
        self.stack.addWidget(self.exposure_page)     # 4
        self.stack.addWidget(self.system_page)       # 5
        self.stack.addWidget(self.device_info_page)  # 6
        self.stack.addWidget(self.language_page)     # 7
        self.stack.addWidget(self.service_page)      # 8
        self.stack.addWidget(self.file_preview_page) # 9
        self.stack.addWidget(self.print_progress_page) # 10
        self.stack.addWidget(self.setting_page)      # 11
        self.stack.addWidget(self.theme_page)        # 12
        self.stack.addWidget(self.leveling_page)    # 13
        self.stack.addWidget(self.material_page)    # 14

        self.setCentralWidget(self.stack)

    def _apply_saved_settings(self):
        """저장된 설정값을 페이지에 적용"""
        # Setting 페이지에 적용
        saved_led_power = self.settings.get_led_power()
        saved_blade_speed = self.settings.get_blade_speed()

        self.setting_page.set_led_power(saved_led_power)
        self.setting_page.set_blade_speed(saved_blade_speed)

        # 선택된 소재 프리셋을 FilePreview에 적용
        preset = self.settings.get_selected_material_preset()
        if preset:
            self.file_preview_page.apply_material(preset)

        print(f"[System] 저장된 설정 적용:")
        print(f"  - LED Power: {saved_led_power}%")
        print(f"  - Blade Speed: {saved_blade_speed}mm/s")
        print(f"  - 선택 소재: {self.settings.get_selected_material()}")

    def _connect_signals(self):
        """시그널 연결"""
        # 메인 페이지
        self.main_page.go_tool.connect(lambda: self._go_to_page(self.PAGE_TOOL))
        self.main_page.go_print.connect(lambda: self._go_to_page(self.PAGE_PRINT))
        self.main_page.go_system.connect(lambda: self._go_to_page(self.PAGE_SYSTEM))
        self.main_page.logo_clicked.connect(self._on_logo_clicked)
        
        # 도구 페이지
        self.tool_page.go_back.connect(lambda: self._go_to_page(self.PAGE_MAIN))
        self.tool_page.go_manual.connect(lambda: self._go_to_page(self.PAGE_MANUAL))
        self.tool_page.go_exposure.connect(lambda: self._go_to_page(self.PAGE_EXPOSURE))
        self.tool_page.go_leveling.connect(self._go_to_leveling)
        self.tool_page.go_setting.connect(lambda: self._go_to_page(self.PAGE_SETTING))
        self.tool_page.go_material.connect(lambda: self._go_to_page(self.PAGE_MATERIAL))

        # 소재 페이지
        self.material_page.go_back.connect(lambda: self._go_to_page(self.PAGE_TOOL))

        # 설정 페이지
        self.setting_page.go_back.connect(lambda: self._go_to_page(self.PAGE_TOOL))
        self.setting_page.led_on.connect(self._setting_led_on)
        self.setting_page.led_off.connect(self._setting_led_off)
        self.setting_page.blade_home.connect(self._setting_blade_home)
        self.setting_page.blade_move.connect(self._setting_blade_move)
        self.setting_page.led_power_changed.connect(self._on_led_power_changed)
        self.setting_page.blade_speed_changed.connect(self._on_blade_speed_changed)
        self.setting_page.y_move.connect(self._setting_y_move)
        self.setting_page.y_home.connect(self._setting_y_home)
        self.setting_page.y_prime_start.connect(self._setting_y_prime_start)
        self.setting_page.y_prime_done.connect(self._setting_y_prime_done)

        # 매뉴얼 페이지
        self.manual_page.go_back.connect(lambda: self._go_to_page(self.PAGE_TOOL))
        self.manual_page.z_move.connect(self._move_z)
        self.manual_page.z_home.connect(self._home_z)
        self.manual_page.x_move.connect(self._move_x)
        self.manual_page.x_home.connect(self._home_x)
        self.manual_page.y_move.connect(self._manual_y_move)
        self.manual_page.y_home.connect(self._manual_y_home)
        
        # 프린트 페이지
        self.print_page.go_back.connect(lambda: self._go_to_page(self.PAGE_MAIN))
        self.print_page.file_selected.connect(self._on_file_selected)
        
        # 노출 테스트 페이지
        self.exposure_page.go_back.connect(self._on_exposure_back)
        self.exposure_page.exposure_start.connect(self._start_exposure)
        self.exposure_page.exposure_stop.connect(self._stop_exposure)

        # 레벨링 페이지
        self.leveling_page.go_back.connect(lambda: self._go_to_page(self.PAGE_TOOL))
        self.leveling_page.z_home.connect(self._leveling_z_home)
        self.leveling_page.x_home.connect(self._leveling_x_home)
        self.leveling_page.x_move.connect(self._leveling_x_move)

        # 시스템 페이지
        self.system_page.go_back.connect(lambda: self._go_to_page(self.PAGE_MAIN))
        self.system_page.go_device_info.connect(lambda: self._go_to_page(self.PAGE_DEVICE_INFO))
        self.system_page.go_language.connect(lambda: self._go_to_page(self.PAGE_LANGUAGE))
        self.system_page.go_service.connect(lambda: self._go_to_page(self.PAGE_SERVICE))
        self.system_page.go_theme.connect(lambda: self._go_to_page(self.PAGE_THEME))

        # 테마 페이지
        self.theme_page.go_back.connect(lambda: self._go_to_page(self.PAGE_SYSTEM))

        # 장치 정보 페이지
        self.device_info_page.go_back.connect(lambda: self._go_to_page(self.PAGE_SYSTEM))
        
        # 언어 설정 페이지
        self.language_page.go_back.connect(lambda: self._go_to_page(self.PAGE_SYSTEM))
        
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
        self.print_progress_page.z_home_requested.connect(self._on_z_home_requested)

    def _go_to_page(self, page_index: int):
        """페이지 전환"""
        self.stack.setCurrentIndex(page_index)
    
    # ==================== 하드웨어 제어 ====================

    def _start_motor_operation(self, operation: str, on_finished=None, **kwargs):
        """모터 작업을 비동기로 시작 (Klipper 큐에 맡김)"""
        # 스레드 및 워커 생성
        thread = QThread()
        worker = MotorWorker(self.motor, operation, **kwargs)
        worker.moveToThread(thread)

        # 시그널 연결
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.error.connect(self._on_motor_error)
        thread.finished.connect(lambda: self._cleanup_thread(thread, worker))

        # 완료 콜백 (레벨링 등)
        if on_finished:
            worker.finished.connect(on_finished)

        # 스레드 시작
        thread.start()

    def _cleanup_thread(self, thread, worker):
        """모터 스레드 정리"""
        if hasattr(self, '_motor_threads') and thread in self._motor_threads:
            self._motor_threads.remove(thread)
        worker.deleteLater()
        thread.deleteLater()

    def _on_motor_error(self, error_msg: str):
        """모터 작업 오류"""
        print(f"[Motor] 오류: {error_msg}")

    def _move_z(self, distance: float):
        """Z축 이동 (비동기)"""
        print(f"[Motor] Z축 이동: {distance}mm")
        self._start_motor_operation("z_move", distance=distance)

    def _home_z(self):
        """Z축 홈 (비동기)"""
        print("[Motor] Z축 홈으로 이동")
        self._start_motor_operation("z_home")

    def _move_x(self, distance: float):
        """X축(블레이드) 이동 (비동기)"""
        print(f"[Motor] X축 이동: {distance}mm")
        self._start_motor_operation("x_move", distance=distance, speed=300)

    def _home_x(self):
        """X축 홈 (비동기)"""
        print("[Motor] X축 홈으로 이동")
        self._start_motor_operation("x_home")

    def _manual_y_move(self, distance: float):
        """Manual 페이지에서 Resin pump 이동"""
        print(f"[Manual] Resin Move: {distance}mm")
        self._start_motor_operation("y_move", distance=distance)

    def _manual_y_home(self):
        """Manual 페이지에서 Resin pump Home"""
        print("[Manual] Resin Home")
        self._start_motor_operation("y_home")

    # ==================== Leveling 페이지 제어 ====================

    def _go_to_leveling(self):
        """레벨링 페이지로 이동 (진입 시 초기화)"""
        self.leveling_page.reset()
        self._go_to_page(self.PAGE_LEVELING)

    def _leveling_z_home(self):
        """레벨링: Z축 홈"""
        print("[Leveling] Z축 홈으로 이동")
        self._start_motor_operation("z_home", on_finished=self.leveling_page.on_motor_finished)

    def _leveling_x_home(self):
        """레벨링: X축 홈"""
        print("[Leveling] X축 홈으로 이동")
        self._start_motor_operation("x_home", on_finished=self.leveling_page.on_motor_finished)

    def _leveling_x_move(self, distance: float, speed: int):
        """레벨링: X축 이동"""
        print(f"[Leveling] X축 {distance}mm 이동 (속도: {speed}mm/min)")
        self._start_motor_operation("x_move", on_finished=self.leveling_page.on_motor_finished, distance=distance, speed=speed)

    def _emergency_stop(self):
        """모든 동작 정지 (Klipper 유지)"""
        print("[STOP] 모든 동작 정지!")
        # 모터 현재 동작 취소 (quickstop - Klipper 유지)
        self.motor.quickstop()
        # LED 끄기 (프로젝터는 끄지 않음 - 앱 실행 동안 계속 ON)
        self.dlp.led_off()
        # 프린트 워커 정지
        if self.print_worker and self.print_worker.isRunning():
            self.print_worker.stop()
    
    def _on_file_selected(self, file_path: str):
        """파일 선택됨 -> ZIP 검증 → 소재 선택 → File Preview로 이동"""
        print(f"[Print] 파일 선택: {file_path}")

        # ZIP 파일 검증
        validation = validate_zip_file(file_path)
        if not validation.is_valid:
            print(f"[Print] ZIP 검증 실패: {validation.error_message}")
            dialog = ZipErrorDialog(validation.error_message, self.print_page)
            dialog.exec()
            return

        # 소재 선택 팝업
        from pages.file_preview_page import MaterialSelectDialog
        dialog = MaterialSelectDialog(self)
        result = dialog.exec()
        if result != QDialog.Accepted or not dialog.get_selected():
            print("[Print] 소재 선택 취소")
            return

        # 선택된 소재 적용
        selected_name = dialog.get_selected()
        self.settings.set_selected_material(selected_name)
        preset = self.settings.get_material_by_name(selected_name)
        print(f"[Print] 소재 선택: {selected_name}")

        # File Preview로 이동
        self.file_preview_page.set_file(file_path)
        self.file_preview_page.apply_material(preset)
        self._go_to_page(self.PAGE_FILE_PREVIEW)
    
    def _on_start_print(self, file_path: str, params: dict):
        """프린트 시작 - 프라이밍 확인 후 진행"""
        print(f"[Print] 프린트 시작 요청: {file_path}")

        priming_pos = self.settings.get_y_priming_position()

        if priming_pos > 0:
            # 프라이밍 완료 → 바로 출력 시작
            print(f"[Print] 프라이밍 위치 사용: {priming_pos}mm")
            self._execute_print(file_path, params, priming_pos)
        else:
            # 프라이밍 미완료 → 알림 후 출력 안 함
            print("[Print] 프라이밍 기록 없음 → 출력 차단")
            alert = SimpleAlert("셋팅페이지에서 프라이밍을 설정하세요.", self)
            alert.exec()
            return

    def _execute_print(self, file_path: str, params: dict, y_priming_position: float):
        """실제 프린트 실행"""
        print(f"[Print] 프린트 실행: {file_path}")
        print(f"  - 파라미터: {params}")
        print(f"  - Resin priming position: {y_priming_position}mm")

        # 썸네일 가져오기
        thumbnail = None
        if hasattr(self.file_preview_page, 'lbl_thumbnail'):
            pixmap = self.file_preview_page.lbl_thumbnail.pixmap()
            if pixmap:
                thumbnail = pixmap

        # 파라미터 추출
        total_layers = params.get('totalLayer', 100)
        blade_speed = params.get('bladeSpeed', 300)
        led_power_percent = params.get('ledPower', 43)
        led_power = int(1023 * led_power_percent / 100)
        leveling_cycles = params.get('levelingCycles', 1)
        blade_cycles = params.get('bladeCycles', 1)

        # Resin 토출 파라미터
        y_dispense_distance = params.get('yDispenseDistance', 1.0)
        y_dispense_speed = params.get('yDispenseSpeed', 300)
        y_dispense_delay = params.get('yDispenseDelay', 2.0)

        # 추가 파라미터 (run.gcode에서 추출된 값)
        estimated_time = int(params.get('estimatedPrintTime', 0))
        layer_height = float(params.get('layerHeight', 0.0))
        bottom_exposure = float(params.get('bottomLayerExposureTime', 0.0))
        normal_exposure = float(params.get('normalExposureTime', 0.0))
        bottom_layer_count = int(params.get('bottomLayerCount', 0))
        lift_height = float(params.get('normalLayerLiftHeight', 5.0))
        lift_speed = int(params.get('normalLayerLiftSpeed', 65))
        drop_speed = int(params.get('normalDropSpeed', 150))

        # Print Progress 페이지로 정보 전달 및 이동
        self.print_progress_page.set_print_info(
            file_path=file_path,
            thumbnail=thumbnail,
            total_layers=total_layers,
            blade_speed=blade_speed,
            led_power=led_power_percent,
            estimated_time=estimated_time,
            layer_height=layer_height,
            bottom_exposure=bottom_exposure,
            normal_exposure=normal_exposure,
            bottom_layer_count=bottom_layer_count,
            blade_cycles=blade_cycles,
            lift_height=lift_height,
            lift_speed=lift_speed,
            drop_speed=drop_speed,
            y_dispense_distance=y_dispense_distance,
            y_dispense_speed=y_dispense_speed,
            y_dispense_delay=y_dispense_delay,
            y_priming_position=y_priming_position,
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
        self.print_worker.resin_empty.connect(self._on_resin_empty)

        # 프로젝터 윈도우에 이미지 표시 연결
        if self.projector_window:
            self.print_worker.show_image.connect(self.projector_window.show_image)
            self.print_worker.clear_image.connect(self.projector_window.clear_screen)

        # PrintProgressPage에 레이어 이미지 업데이트 연결
        self.print_worker.show_image.connect(self.print_progress_page.update_layer_image)

        # 프린트 시작
        self.print_worker.start_print(
            file_path=file_path,
            params=params,
            blade_speed=blade_speed,
            led_power=led_power,
            leveling_cycles=leveling_cycles,
            blade_cycles=blade_cycles,
            y_dispense_distance=y_dispense_distance,
            y_dispense_speed=y_dispense_speed,
            y_dispense_delay=y_dispense_delay,
            y_priming_position=y_priming_position,
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

        # 프로젝터 윈도우 닫기
        if self.projector_window:
            self.projector_window.close()

        # PrintProgressPage에서 에러 표시 및 종료 버튼 표시
        self.print_progress_page.show_error(message)

    def _on_resin_empty(self):
        """Resin 부족 알림 (Y=0 도달)"""
        print("[Print] Resin empty 알림")

        from pages.file_preview_page import ConfirmDialog
        dialog = ConfirmDialog(
            "Resin Empty",
            "Resin is depleted.\nContinue printing?",
            self
        )
        # "Delete" 텍스트를 "NO"로, "Cancel"을 "OK"로 변경
        dialog.btn_confirm.setText("NO")
        dialog.btn_cancel.setText("OK")

        result = dialog.exec()

        if result == 0:
            # Cancel(OK) 클릭 → Resin 토출 없이 프린팅 계속
            print("[Print] Resin empty → OK: manual supply mode")
            if self.print_worker:
                self.print_worker.disable_y_dispensing()
        else:
            # Confirm(NO) 클릭 → 프린팅 중지
            print("[Print] Resin empty → NO: stop printing")
            if self.print_worker:
                self.print_worker.stop_by_resin_empty()

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

    def _on_z_home_requested(self):
        """Z축 홈 요청 (프린트 종료 후 사용자 선택)"""
        print("[Motor] Z축 홈으로 이동 (사용자 요청)")
        self.motor.z_home()

    def _on_file_deleted(self, file_path: str):
        """파일 삭제됨"""
        print(f"[Print] 파일 삭제됨: {file_path}")
    
    def _start_exposure(self, pattern: str, time: float):
        """노출 테스트 시작"""
        print(f"[NVR] 노출 테스트 시작")
        print(f"  - 패턴: {pattern}")
        print(f"  - 시간: {time}초")

        # 1. LED OFF 먼저 (이전 상태가 켜져 있을 수 있음)
        self.dlp.led_off()

        # 2. 프로젝터 윈도우에 패턴 표시 (프로젝터는 이미 ON 상태)
        if self.projector_window is None:
            self.projector_window = ProjectorWindow(screen_index=1)

        screens = QApplication.screens()
        if len(screens) > 1:
            self.projector_window.show_on_screen(1)

            if pattern == "clean":
                self.projector_window.show_white_screen()
            elif pattern == "test_image":
                self.projector_window.show_test_image()
            else:
                self.projector_window.show_test_pattern(pattern)

            QApplication.processEvents()

        # 3. LED ON (프로젝터는 앱 시작 시 이미 켜져 있음)
        self.dlp.led_on(440)

    def _stop_exposure(self):
        """노출 테스트 정지"""
        print("[NVR] 노출 테스트 정지")
        self.dlp.led_off()

        if self.projector_window:
            self.projector_window.clear_screen()

    def _on_exposure_back(self):
        """Exposure 페이지에서 나갈 때"""
        self._stop_exposure()
        if self.projector_window:
            self.projector_window.close()
        self._go_to_page(self.PAGE_TOOL)

    # ==================== Setting 페이지 제어 ====================

    def _setting_led_on(self, power_percent: int):
        """Setting 페이지에서 LED ON"""
        # 퍼센트를 NVM 값으로 변환 (100% = 1023)
        led_power = int(1023 * power_percent / 100)
        led_power = max(91, min(1023, led_power))  # 범위 제한

        print(f"[Setting] LED ON 시도")
        print(f"  - Power: {power_percent}% (NVM: {led_power})")

        # 1. 프로젝터 윈도우에 1.png 표시 (프로젝터는 이미 ON 상태)
        if self.projector_window is None:
            self.projector_window = ProjectorWindow(screen_index=1)

        screens = QApplication.screens()
        if len(screens) > 1:
            self.projector_window.show_on_screen(1)
        else:
            self.projector_window.show_on_screen(0)

        self.projector_window.show_test_image()  # 1.png 표시
        QApplication.processEvents()

        # 2. LED ON (프로젝터는 앱 시작 시 이미 켜져 있음)
        self.dlp.led_on(led_power)

    def _setting_led_off(self):
        """Setting 페이지에서 LED OFF"""
        print("[Setting] LED OFF")
        self.dlp.led_off()
        # 프로젝터는 끄지 않음 (앱 실행 동안 계속 ON)

        if self.projector_window:
            self.projector_window.clear_screen()
            self.projector_window.close()

    def _setting_blade_home(self):
        """Setting 페이지에서 Blade Home"""
        print("[Setting] Blade Home")
        self.motor.x_home()

    def _setting_blade_move(self):
        """Setting 페이지에서 Blade Move (140→0 또는 0→140)"""
        # 현재 X 위치 확인
        _, x_pos = self.motor.get_position()

        # Blade 속도 가져오기 (mm/s → mm/min 변환)
        blade_speed_mms = self.setting_page.get_blade_speed()
        blade_speed = blade_speed_mms * 60  # mm/min으로 변환

        print(f"[Setting] Blade Move (현재: {x_pos:.1f}mm, 속도: {blade_speed_mms}mm/s)")

        if x_pos > 70:  # 140에 가까우면 0으로
            print("[Setting] Blade 140 → 0mm 이동")
            self.motor.x_move_absolute(0, blade_speed)
        else:  # 0에 가까우면 140으로
            print("[Setting] Blade 0 → 140mm 이동")
            self.motor.x_move_absolute(140, blade_speed)

    def _setting_y_move(self, distance: float):
        """Setting 페이지에서 Resin pump 이동"""
        print(f"[Setting] Resin Move: {distance}mm")
        self._start_motor_operation("y_move", distance=distance)

    def _setting_y_home(self):
        """Setting 페이지에서 Resin pump Home"""
        print("[Setting] Resin Home")
        self._start_motor_operation("y_home")

    def _setting_y_prime_start(self):
        """Setting 페이지에서 프라이밍 시작 (G28 Y 홈잉으로 절대 0점 확보)"""
        print("[Setting] Resin Priming Start - G28 Y homing...")
        self._start_motor_operation(
            "y_home",
            on_finished=self.setting_page.y_panel.on_homing_completed
        )

    def _setting_y_prime_done(self):
        """Setting 페이지에서 프라이밍 완료 (Klipper 실제 좌표 조회 후 저장)"""
        self.motor.get_position()  # Klipper에서 실제 위치 조회 → _y_position 갱신
        y_pos = self.motor._y_position
        print(f"[Setting] Resin Priming Done - Position: {y_pos}mm (Klipper)")
        self.settings.set_y_priming_position(y_pos)

    # ==================== 설정 저장/동기화 ====================

    def _on_led_power_changed(self, power: int):
        """LED Power 변경 시 저장"""
        print(f"[Setting] LED Power 변경: {power}%")
        self.settings.set_led_power(power)

    def _on_blade_speed_changed(self, speed: int):
        """Blade Speed 변경 시 저장"""
        print(f"[Setting] Blade Speed 변경: {speed}mm/s")
        self.settings.set_blade_speed(speed)

    # ==================== 시스템 메뉴 ====================

    def _send_gcode(self, gcode: str):
        """G-code 전송 (Moonraker API)"""
        # TODO: Moonraker API 연동
        pass

    # ==================== 테마 변경 ====================

    def _on_theme_changed(self, theme_name: str):
        """테마 변경 시 UI 새로고침"""
        print(f"[Theme] 테마 변경: {theme_name}")

        # 글로벌 스타일 재적용
        QApplication.instance().setStyleSheet(get_global_style())

        # 모든 페이지를 새로 생성하여 교체
        self._rebuild_pages()

    def _rebuild_pages(self):
        """모든 페이지를 새로 생성하여 테마 적용"""
        # 현재 페이지 인덱스 저장
        current_index = self.stack.currentIndex()

        # 기존 페이지들 제거
        while self.stack.count() > 0:
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()

        # 페이지 재생성
        self._setup_pages()
        self._connect_signals()

        # 저장된 설정 적용
        self._apply_saved_settings()

        # 이전 페이지로 복원
        if current_index < self.stack.count():
            self.stack.setCurrentIndex(current_index)

        print("[Theme] UI 새로고침 완료")

    # ==================== 키오스크/관리자 모드 ====================

    def _on_logo_clicked(self):
        """로고 클릭 - 키오스크 관리자에 전달"""
        self.kiosk_manager.on_logo_clicked()

    def _on_admin_mode_changed(self, enabled: bool):
        """관리자 모드 변경 시"""
        if enabled:
            # 관리자 모드 활성화 - 커서 표시
            self.setCursor(Qt.ArrowCursor)
            print("[Admin] 관리자 모드 - Alt+Tab, Esc 등 허용")
            alert = SimpleAlert("관리자 모드 활성화", self)
            alert.exec()
        else:
            # 관리자 모드 비활성화 - 키오스크 모드면 커서 숨김
            if self.kiosk_manager.is_enabled:
                self.setCursor(Qt.BlankCursor)
            print("[Admin] 일반 모드 - 단축키 차단")
            alert = SimpleAlert("관리자 모드 해제", self)
            alert.exec()

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

        # 하드웨어 정리 (LED OFF, 프로젝터 OFF)
        self.dlp.led_off()
        self.dlp.projector_off()
        print("[System] 프로젝터 OFF (앱 종료)")

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

    # 글로벌 스타일 적용 (동적 함수 사용 - 저장된 테마 반영)
    app.setStyleSheet(get_global_style())

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
