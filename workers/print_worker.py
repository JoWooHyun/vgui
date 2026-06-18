"""
VERICOM DLP 3D Printer - Print Worker
QThread 기반 프린팅 시퀀스 실행
"""

import time
import zipfile
from enum import Enum, auto
from typing import Optional, Dict, Any
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition
from PySide6.QtGui import QPixmap, QImage

# 컨트롤러 임포트
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from controllers.motor_controller import MotorController
    from controllers.dlp_controller import DLPController
    from controllers.gcode_parser import GCodeParser, PrintParameters
except ImportError:
    # 상대 임포트 시도
    from ..controllers.motor_controller import MotorController
    from ..controllers.dlp_controller import DLPController
    from ..controllers.gcode_parser import GCodeParser, PrintParameters


class PrintStatus(Enum):
    """프린트 상태"""
    IDLE = auto()
    INITIALIZING = auto()
    LEVELING = auto()
    PRINTING = auto()
    PAUSED = auto()
    STOPPING = auto()
    COMPLETED = auto()
    ERROR = auto()


@dataclass
class PrintJob:
    """프린트 작업 정보"""
    file_path: str
    params: PrintParameters
    blade_speed: int = 300   # mm/min (구간1: start→boundary)
    blade_speed2: int = 1200 # mm/min (구간2: boundary→end)
    blade_boundary: float = 60.0  # 구간 경계 위치 (mm)
    blade_start: float = 0.0  # 블레이드 시작 위치 (mm)
    blade_end: float = 130.0  # 블레이드 끝 위치 (mm)
    led_power: int = 440
    z_offset: float = 0.0    # Z 오프셋 (mm)
    settle_time: float = 0.0 # 초기+첫레이어 토출 후 대기 (초)
    initial_leveling: bool = True  # 초기 평탄화 ON/OFF
    leveling_cycles: int = 1
    blade_cycles: int = 1  # 매 레이어 블레이드 왕복 횟수
    y_dispense_distance: float = 1.0   # Resin 토출 거리 (mm/레이어)
    y_dispense_speed: int = 300        # Resin 토출 속도 (mm/min)
    y_dispense_delay: float = 2.0      # Resin 토출 후 대기 (초)
    y_priming_position: float = 0.0    # 프라이밍 완료 위치 (mm, 0이면 미완료)
    y_pull_distance: float = 0.0       # Resin 되돌리기 거리 (mm, 0=비활성)
    y_pull_delay: float = 2.0          # Pull 구간 시간 (초) → speed 자동계산
    y_return_distance: float = 0.0     # 다시 밀기 거리 (mm, 0=비활성)
    y_return_delay: float = 2.0        # Return 구간 시간 (초) → speed 자동계산


class PrintWorker(QThread):
    """
    프린팅 시퀀스를 실행하는 워커 스레드

    시그널:
        status_changed: 상태 변경 시
        progress_updated: 레이어 진행 시 (current, total)
        layer_started: 레이어 시작 시 (layer_index)
        error_occurred: 에러 발생 시 (message)
        print_completed: 프린트 완료 시
        print_stopped: 프린트 중지 시
    """

    # 시그널 정의
    status_changed = Signal(str)  # PrintStatus name
    progress_updated = Signal(int, int)  # current, total
    layer_started = Signal(int)  # layer_index
    error_occurred = Signal(str)  # error message
    print_completed = Signal()
    print_stopped = Signal()
    resin_empty = Signal()  # Resin 부족 알림 (position_min=0 도달)
    priming_requested = Signal()  # 프라이밍 요청 (프린트 중 프라이밍 필요 시)

    # 이미지 표시 요청 시그널 (ProjectorWindow로 전달)
    show_image = Signal(object)  # QPixmap
    clear_image = Signal()

    def __init__(self,
                 motor: Optional[MotorController] = None,
                 dlp: Optional[DLPController] = None,
                 parent=None):
        super().__init__(parent)

        # 컨트롤러
        self.motor = motor
        self.dlp = dlp

        # 상태
        self._status = PrintStatus.IDLE
        self._is_paused = False
        self._is_stopped = False

        # 동기화
        self._mutex = QMutex()
        self._pause_condition = QWaitCondition()
        self._resin_mutex = QMutex()
        self._resin_condition = QWaitCondition()

        # Resin 토출 상태
        self._y_position = 0.0           # Resin pump 현재 위치
        self._y_dispensing_disabled = False  # True면 토출 스킵 (수동 공급 모드)
        self._y_resin_waiting = False     # Resin 부족 응답 대기 중

        # 현재 작업
        self._job: Optional[PrintJob] = None

        # 시뮬레이션 모드
        self.simulation = False

    # ==================== 상태 관리 ====================

    @property
    def status(self) -> PrintStatus:
        return self._status

    def _set_status(self, status: PrintStatus):
        self._status = status
        self.status_changed.emit(status.name)
        print(f"[PrintWorker] 상태 변경: {status.name}")

    # ==================== 제어 메서드 ====================

    def start_print(self, file_path: str, params: Dict[str, Any],
                   blade_speed: int = 300, blade_speed2: int = 1200,
                   blade_boundary: float = 60.0,
                   blade_start: float = 0.0,
                   blade_end: float = 130.0, led_power: int = 440,
                   z_offset: float = 0.0, settle_time: float = 0.0,
                   initial_leveling: bool = True,
                   leveling_cycles: int = 1, blade_cycles: int = 1,
                   y_dispense_distance: float = 1.0,
                   y_dispense_speed: int = 300,
                   y_dispense_delay: float = 2.0,
                   y_priming_position: float = 0.0,
                   y_pull_distance: float = 0.0,
                   y_pull_delay: float = 2.0,
                   y_return_distance: float = 0.0,
                   y_return_delay: float = 2.0):
        """
        프린트 시작

        Args:
            file_path: ZIP 파일 경로
            params: 프린트 파라미터 딕셔너리
            blade_speed: 블레이드 속도 (mm/min)
            blade_start: 블레이드 시작 위치 (mm, 0~10)
            blade_end: 블레이드 끝 위치 (mm, 120~130)
            led_power: LED 밝기 (91~1023)
            leveling_cycles: 레진 평탄화 횟수
            blade_cycles: 매 레이어 블레이드 왕복 횟수 (1~3)
            y_dispense_distance: Y축 토출 거리 (mm/레이어)
            y_dispense_speed: Y축 토출 속도 (mm/min)
            y_dispense_delay: Y축 토출 후 대기 (초)
            y_priming_position: 프라이밍 완료 위치 (mm, 0이면 미완료)
            y_pull_distance: Resin 되돌리기 거리 (mm, 0=비활성)
            y_pull_delay: Pull 구간 시간 (초)
            y_return_distance: 다시 밀기 거리 (mm, 0=비활성)
            y_return_delay: Return 구간 시간 (초)
        """
        if self.isRunning():
            print("[PrintWorker] 이미 실행 중")
            return

        # PrintParameters 객체 생성
        print_params = PrintParameters()
        for key, value in params.items():
            if hasattr(print_params, key):
                setattr(print_params, key, value)

        # 작업 생성
        self._job = PrintJob(
            file_path=file_path,
            params=print_params,
            blade_speed=blade_speed,
            blade_speed2=blade_speed2,
            blade_boundary=blade_boundary,
            blade_start=blade_start,
            blade_end=blade_end,
            led_power=led_power,
            z_offset=z_offset,
            settle_time=settle_time,
            initial_leveling=initial_leveling,
            leveling_cycles=leveling_cycles,
            blade_cycles=blade_cycles,
            y_dispense_distance=y_dispense_distance,
            y_dispense_speed=y_dispense_speed,
            y_dispense_delay=y_dispense_delay,
            y_priming_position=y_priming_position,
            y_pull_distance=y_pull_distance,
            y_pull_delay=y_pull_delay,
            y_return_distance=y_return_distance,
            y_return_delay=y_return_delay,
        )

        # 플래그 초기화
        self._is_paused = False
        self._is_stopped = False
        self._y_position = y_priming_position  # 프라이밍 위치에서 시작
        self._y_dispensing_disabled = False
        self._y_resin_waiting = False

        # 스레드 시작
        self.start()

    def pause(self):
        """일시정지"""
        self._mutex.lock()
        self._is_paused = True
        self._mutex.unlock()
        self._set_status(PrintStatus.PAUSED)
        print("[PrintWorker] 일시정지")

    def resume(self):
        """재개"""
        self._mutex.lock()
        self._is_paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()
        self._set_status(PrintStatus.PRINTING)
        print("[PrintWorker] 재개")

    def stop(self):
        """정지"""
        self._mutex.lock()
        self._is_stopped = True
        self._is_paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()
        # Resin 대기 중이면 깨우기
        self._resin_mutex.lock()
        self._y_resin_waiting = False
        self._resin_condition.wakeAll()
        self._resin_mutex.unlock()
        self._set_status(PrintStatus.STOPPING)
        print("[PrintWorker] 정지 요청")

    def disable_y_dispensing(self):
        """Resin empty → OK: 토출 비활성화, 수동 공급 모드로 계속"""
        self._y_dispensing_disabled = True
        self._resin_mutex.lock()
        self._y_resin_waiting = False
        self._resin_condition.wakeAll()
        self._resin_mutex.unlock()
        # 수동 공급 모드: 블레이드를 0mm으로 이동 (공간 확보)
        print("[PrintWorker] Resin dispensing disabled (manual supply mode)")
        self._motor_x_move(0, 3000)
        print("[PrintWorker] Blade moved to 0mm for manual supply")

    def stop_by_resin_empty(self):
        """Resin empty → NO: 프린팅 중지"""
        self._resin_mutex.lock()
        self._y_resin_waiting = False
        self._resin_condition.wakeAll()
        self._resin_mutex.unlock()
        self.stop()
        print("[PrintWorker] Stopped by resin empty")

    def refill_resin(self, new_y_position: float):
        """주사기 교체 후 새 Y 위치로 재개"""
        self._y_position = new_y_position
        self._y_dispensing_disabled = False
        self._resin_mutex.lock()
        self._y_resin_waiting = False
        self._resin_condition.wakeAll()
        self._resin_mutex.unlock()
        print(f"[PrintWorker] Resin refilled, new Y position: {new_y_position}mm")

    # ==================== 메인 루프 ====================

    def run(self):
        """프린팅 시퀀스 실행"""
        if not self._job:
            self.error_occurred.emit("프린트 작업이 없습니다")
            return

        try:
            self._run_print_sequence()
        except Exception as e:
            self._set_status(PrintStatus.ERROR)
            self.error_occurred.emit(str(e))
            print(f"[PrintWorker] 오류: {e}")
        finally:
            self._cleanup()

    def _run_print_sequence(self):
        """프린팅 시퀀스"""
        job = self._job
        params = job.params

        # 1. 초기화
        self._set_status(PrintStatus.INITIALIZING)
        print(f"[PrintWorker] 프린트 시작: {job.file_path}")
        print(f"  - 총 레이어: {params.totalLayer}")
        print(f"  - 블레이드 속도: {job.blade_speed} mm/min")
        print(f"  - 블레이드 범위: {job.blade_start}~{job.blade_end} mm")
        print(f"  - LED 파워: {job.led_power}")

        # 컨트롤러 설정 (시뮬레이션 모드가 아닐 때)
        # 주의: DLP는 main.py에서 이미 초기화됨, 다시 초기화하면 안됨
        if not self.simulation:
            if self.dlp and self.dlp.is_initialized:
                self.dlp.set_brightness(job.led_power)

            if self.motor:
                self.motor.connect()
                # 이전 일시정지 상태 초기화
                self.motor.klipper_clear_pause()

        # X축 홈 → 시작 위치
        if self._check_stopped():
            return
        if not self._motor_x_home():
            self.error_occurred.emit("X축 홈 이동 실패")
            self._is_stopped = True
            return
        if job.blade_start > 0:
            if not self._motor_x_move(job.blade_start, job.blade_speed):
                self.error_occurred.emit(f"X축 시작위치({job.blade_start}mm) 이동 실패")
                self._is_stopped = True
                return

        # 초기 평탄화 (ON일 때만 실행)
        if job.initial_leveling:
            # Z축 홈 → 평탄화용 높이 (z_offset)
            if self._check_stopped():
                return
            if not self._motor_z_home():
                self.error_occurred.emit("Z축 홈 이동 실패")
                self._is_stopped = True
                return
            leveling_z = job.z_offset
            if leveling_z > 0:
                if not self._motor_z_move(leveling_z):
                    self.error_occurred.emit(f"Z축 {leveling_z}mm 이동 실패")
                    self._is_stopped = True
                    return

            # Resin: 프라이밍 위치에서 시작
            print(f"[PrintWorker] Resin start position: {job.y_priming_position}mm")
            self._y_position = job.y_priming_position

            # 2. 평탄화 전 첫 레진 토출 (3mm/s 고정속도로 3단계 토출)
            INITIAL_DISPENSE_SPEED = 180     # mm/min (3mm/s)
            if not self._y_dispensing_disabled and self._y_position > 0:
                if self._check_stopped():
                    return
                if not self._dispense_3step(-1, job, push_speed_override=INITIAL_DISPENSE_SPEED):
                    return

            # Settle time 대기 (초기 토출)
            if job.settle_time > 0:
                print(f"[PrintWorker] 초기 토출 settle time: {job.settle_time}초")
                if not self._wait_interruptible(job.settle_time):
                    return

            # 3. 레진 평탄화 (편도: start→end)
            self._set_status(PrintStatus.LEVELING)
            if self._check_stopped():
                return
            if not self._motor_x_move(job.blade_end, job.blade_speed):
                self.error_occurred.emit("초기 평탄화 실패")
                self._is_stopped = True
                return
            # Z 올림 + X 복귀
            if not self._motor_z_move(leveling_z + 3.0):
                self.error_occurred.emit("초기 평탄화 Z 리프트 실패")
                self._is_stopped = True
                return
            if not self._motor_x_move(job.blade_start, 3000):
                self.error_occurred.emit("초기 평탄화 X 복귀 실패")
                self._is_stopped = True
                return
            # Z 홈 복귀
            if not self._motor_z_home():
                self.error_occurred.emit("초기 평탄화 Z 홈 복귀 실패")
                self._is_stopped = True
                return
        else:
            print("[PrintWorker] 초기 평탄화 OFF — 스킵")
            self._y_position = job.y_priming_position

        # 3. 프로젝터는 앱 시작 시 이미 ON 상태 (별도 동작 불필요)

        # 4. 메인 프린팅 루프
        self._set_status(PrintStatus.PRINTING)
        total_layers = params.totalLayer

        for layer_idx in range(total_layers):
            # 정지 체크
            if self._check_stopped():
                break

            # 일시정지 체크
            self._check_paused()
            if self._check_stopped():
                break

            # 레이어 시작
            self.layer_started.emit(layer_idx)
            self.progress_updated.emit(layer_idx + 1, total_layers)

            # 레이어 처리 (실패 시 루프 종료)
            if not self._process_layer(layer_idx, job):
                break

        # 5. 완료 또는 정지
        if self._is_stopped:
            self._set_status(PrintStatus.STOPPING)
            self.print_stopped.emit()
        else:
            self._set_status(PrintStatus.COMPLETED)
            self.print_completed.emit()

    def _process_layer(self, layer_idx: int, job: PrintJob) -> bool:
        """
        단일 레이어 처리

        Flow:
        1. Z축 레이어 높이로 이동
        2. Resin 토출 + 대기
        3. X축 시작→끝 (평탄화)
        4. 이미지 투영 → LED ON → 노광 → LED OFF
        5. Z축 리프트 (+5mm)
        6. X축 끝→시작 (복귀)

        Returns:
            bool: 성공 시 True, 실패 시 False (이미지 로드 실패 등)
        """
        params = job.params

        # 바닥 레이어 vs 일반 레이어
        is_bottom = layer_idx < params.bottomLayerCount
        if is_bottom:
            exposure_time = params.bottomLayerExposureTime
        else:
            exposure_time = params.normalExposureTime

        # Z축 위치 계산
        z_position = job.z_offset + (layer_idx + 1) * params.layerHeight

        # 1. Z축 레이어 높이로 이동
        if not self._motor_z_move(z_position):
            self.error_occurred.emit(f"레이어 {layer_idx}: Z축 이동 실패")
            self._is_stopped = True
            return False

        # 2. Resin 토출 (3단계: Push → Pull → Return)
        # 소진 감지는 _dispense_3step() 내부에서 Push 직후 처리
        if job.y_dispense_distance > 0:
            if self._y_dispensing_disabled:
                # 수동 공급 모드: Y축 스킵, delay만 유지
                print(f"[PrintWorker] Layer {layer_idx}: Manual feed mode — Y skip, waiting {job.y_dispense_delay}s")
                if not self._wait_interruptible(job.y_dispense_delay):
                    return False
            else:
                # 정상 토출 (소진 시 _dispense_3step 내부에서 resin_empty 처리)
                if not self._dispense_3step(layer_idx, job):
                    return False

        # Settle time 대기 (첫 레이어만)
        if layer_idx == 0 and job.settle_time > 0:
            print(f"[PrintWorker] Layer 0 settle time: {job.settle_time}초")
            if not self._wait_interruptible(job.settle_time):
                return True

        # 3. X축 평탄화 (2구간: start→boundary→end)
        if not self._motor_x_move(job.blade_boundary, job.blade_speed):
            self.error_occurred.emit(f"레이어 {layer_idx}: X축 평탄화(구간1) 실패")
            self._is_stopped = True
            return False
        if not self._motor_x_move(job.blade_end, job.blade_speed2):
            self.error_occurred.emit(f"레이어 {layer_idx}: X축 평탄화(구간2) 실패")
            self._is_stopped = True
            return False

        # 정지/일시정지 체크 (LED ON 전에)
        if self._check_stopped():
            return True
        self._check_paused()
        if self._check_stopped():
            return True

        # 4. 이미지 투영 (실패 시 프린트 중지)
        if not self._show_layer_image(job.file_path, layer_idx):
            self._mutex.lock()
            self._is_stopped = True
            self._mutex.unlock()
            return False

        # 5. LED ON + 노광 (블레이드 끝 위치 = 빛 안 가림)
        self._dlp_led_on(job.led_power)
        self._wait_exposure(exposure_time)

        # 6. LED OFF
        self._dlp_led_off()
        self.clear_image.emit()

        # LED OFF 후 일시정지/정지 체크
        if self._check_stopped():
            return True
        self._check_paused()
        if self._check_stopped():
            return True

        # 7. Z축 리프트 (+3mm)
        z_lift_position = z_position + 3.0
        if not self._motor_z_move(z_lift_position):
            self.error_occurred.emit(f"레이어 {layer_idx}: Z축 리프트 실패")
            self._is_stopped = True
            return False

        # 8. X축 시작 위치 복귀
        # 복귀는 평탄화가 아니므로 빠른 고정 속도 사용 (50mm/s = 3000mm/min)
        x_return_position = job.blade_start
        if not self._motor_x_move(x_return_position, 3000):
            self.error_occurred.emit(f"레이어 {layer_idx}: X축 홈 복귀 실패")
            self._is_stopped = True
            return False

        return True

    # ==================== 하드웨어 제어 래퍼 ====================

    def _motor_z_home(self) -> bool:
        """Z축 홈"""
        print("[PrintWorker] Z축 홈 이동")
        if self.motor and not self.simulation:
            return self.motor.z_home()
        else:
            time.sleep(0.5)  # 시뮬레이션
            return True

    def _motor_x_home(self, force: bool = True) -> bool:
        """
        X축 홈

        Args:
            force: True면 캐시 상태와 관계없이 강제 홈잉 (기본값 True)
        """
        print("[PrintWorker] X축 홈 이동")
        if self.motor and not self.simulation:
            return self.motor.x_home(force=force)
        else:
            time.sleep(0.3)
            return True

    def _motor_z_move(self, position: float, speed: int = 300) -> bool:
        """Z축 이동"""
        if self.motor and not self.simulation:
            return self.motor.z_move_absolute(position, speed)
        else:
            time.sleep(0.1)
            return True

    def _motor_x_move(self, position: float, speed: int = 300) -> bool:
        """X축 이동"""
        if self.motor and not self.simulation:
            return self.motor.x_move_absolute(position, speed)
        else:
            time.sleep(0.2)
            return True

    def _motor_y_home(self) -> bool:
        """Resin pump 홈"""
        print("[PrintWorker] Resin pump homing")
        if self.motor and not self.simulation:
            return self.motor.y_home()
        else:
            time.sleep(0.3)
            return True

    def _motor_y_move(self, distance: float, speed: int = 300) -> tuple:
        """Resin pump 상대 이동 → (success, actual_distance) 반환"""
        if self.motor and not self.simulation:
            before = self.motor._y_position
            success = self.motor.y_move_relative(distance, speed)
            actual = self.motor._y_position - before
            return success, actual
        else:
            time.sleep(0.1)
            return True, distance

    def _dlp_projector_on(self):
        """프로젝터 ON"""
        print("[PrintWorker] 프로젝터 ON")
        if self.dlp and not self.simulation:
            self.dlp.projector_on()

    def _dlp_projector_off(self):
        """프로젝터 OFF"""
        print("[PrintWorker] 프로젝터 OFF")
        if self.dlp and not self.simulation:
            self.dlp.projector_off()

    def _dlp_led_on(self, brightness: int):
        """LED ON"""
        if self.dlp and not self.simulation:
            self.dlp.led_on(brightness)

    def _dlp_led_off(self):
        """LED OFF"""
        if self.dlp and not self.simulation:
            self.dlp.led_off()

    def _show_layer_image(self, zip_path: str, layer_idx: int) -> bool:
        """
        레이어 이미지 표시

        Args:
            zip_path: ZIP 파일 경로
            layer_idx: 레이어 인덱스

        Returns:
            bool: 성공 시 True, 실패 시 False
        """
        max_retries = 3
        retry_delay = 0.5  # 500ms

        for attempt in range(max_retries):
            try:
                image_data = GCodeParser.get_layer_image(zip_path, layer_idx)
                if image_data:
                    qimage = QImage.fromData(image_data)
                    if qimage.isNull():
                        raise ValueError(f"이미지 데이터 손상 (레이어 {layer_idx})")
                    pixmap = QPixmap.fromImage(qimage)
                    self.show_image.emit(pixmap)
                    return True
                else:
                    raise FileNotFoundError(f"레이어 {layer_idx} 이미지를 찾을 수 없음")
            except Exception as e:
                print(f"[PrintWorker] 이미지 로드 오류 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    # 모든 재시도 실패
                    error_msg = f"레이어 {layer_idx} 이미지 로드 실패: {e}"
                    print(f"[PrintWorker] 치명적 오류: {error_msg}")
                    self.error_occurred.emit(error_msg)
                    return False

        return False

    # ==================== 토출 헬퍼 ====================

    def _wait_interruptible(self, seconds: float) -> bool:
        """지정 시간 대기, 정지 시 False 반환"""
        start = time.monotonic()
        while (time.monotonic() - start) < seconds:
            if self._check_stopped():
                return False
            time.sleep(0.1)
        return True

    def _dispense_3step(self, layer_idx: int, job: PrintJob,
                        push_speed_override: int = 0) -> bool:
        """
        3단계 토출: Push → [Resin Delay] → Pull → Return
        - Pull/Return 거리가 0이면 해당 단계 스킵
        - layer_idx=-1이면 초기 토출
        """
        label = "Initial" if layer_idx < 0 else f"Layer {layer_idx}"
        push_speed = push_speed_override if push_speed_override else job.y_dispense_speed

        # === Step 1: Push ===
        push_dist = -job.y_dispense_distance
        success, actual = self._motor_y_move(push_dist, push_speed)
        if not success:
            self.error_occurred.emit(f"{label}: Resin push failed")
            self._is_stopped = True
            return False
        self._y_position += actual
        print(f"[PrintWorker] {label}: Push {actual:.2f}mm (pos: {self._y_position:.1f}mm)")

        # Push 후 소진 체크 — 홈 센서로 실제 소진 확인
        if self._y_position <= 0:
            # 홈 센서로 물리적 소진 확인
            endstop_triggered = self.motor.query_y_endstop() if self.motor and not self.simulation else True

            if not endstop_triggered:
                # 탈조 발생 — 좌표 보정 후 홈 센서까지 재시도
                print(f"[PrintWorker] {label}: Position ≤ 0 but endstop NOT triggered — stall detected, retrying")
                retry_distance = 10.0
                max_retries = 15

                for retry in range(max_retries):
                    if self._check_stopped():
                        return False
                    # 좌표를 retry_distance로 속여서 다시 밀 수 있게 함
                    if self.motor:
                        self.motor.y_reset_position(retry_distance)
                    self._y_position = retry_distance

                    # 다시 토출 시도
                    success, actual = self._motor_y_move(-retry_distance, push_speed)
                    if not success:
                        self.error_occurred.emit(f"{label}: Resin retry push failed")
                        self._is_stopped = True
                        return False
                    self._y_position += actual

                    # 홈 센서 재확인
                    endstop_triggered = self.motor.query_y_endstop() if self.motor and not self.simulation else True
                    if endstop_triggered:
                        print(f"[PrintWorker] {label}: Endstop triggered after {retry + 1} retries — resin truly empty")
                        break
                    print(f"[PrintWorker] {label}: Retry {retry + 1}/{max_retries} — endstop still open")

                if not endstop_triggered:
                    print(f"[PrintWorker] {label}: Max retries reached — treating as empty")

            print(f"[PrintWorker] {label}: Resin exhausted (pos: {self._y_position:.1f}mm, endstop: {'triggered' if endstop_triggered else 'max retries'})")
            self._y_resin_waiting = True
            self.resin_empty.emit()
            self._resin_mutex.lock()
            while self._y_resin_waiting and not self._is_stopped:
                self._resin_condition.wait(self._resin_mutex, 1000)
            self._resin_mutex.unlock()
            if self._check_stopped():
                return False
            if self._y_dispensing_disabled:
                # 수동배급 선택 → delay만 대기 후 계속
                if not self._wait_interruptible(job.y_dispense_delay):
                    return False
                return True
            else:
                # 리필 완료 → delay 대기 후 Pull/Return 진행
                if not self._wait_interruptible(job.y_dispense_delay):
                    return False
                # Pull/Return은 아래 로직에서 계속 진행

        # === Resin Delay: Push 후 대기 ===
        if job.y_dispense_delay > 0:
            print(f"[PrintWorker] {label}: Resin Delay {job.y_dispense_delay}s")
            if not self._wait_interruptible(job.y_dispense_delay):
                return False

        # Pull 거리 없으면 여기서 종료
        if job.y_pull_distance <= 0:
            return True

        # === Step 2: Pull (speed = dist / delay 자동계산) ===
        if job.y_pull_delay > 0:
            pull_speed = int(job.y_pull_distance / job.y_pull_delay * 60)
            if pull_speed < 1:
                pull_speed = 1
        else:
            pull_speed = 600
        pull_start = time.monotonic()
        print(f"[PrintWorker] {label}: Pull +{job.y_pull_distance}mm @ {pull_speed}mm/min (delay {job.y_pull_delay}s)")
        success, actual_pull = self._motor_y_move(job.y_pull_distance, pull_speed)
        if not success:
            self.error_occurred.emit(f"{label}: Resin pull failed")
            self._is_stopped = True
            return False
        self._y_position += actual_pull
        print(f"[PrintWorker] {label}: Pull done +{actual_pull:.2f}mm (pos: {self._y_position:.1f}mm)")

        # Pull delay 남은 시간 대기
        pull_remaining = job.y_pull_delay - (time.monotonic() - pull_start)
        if pull_remaining > 0:
            if not self._wait_interruptible(pull_remaining):
                return False

        # Return 거리 없으면 여기서 종료
        if job.y_return_distance <= 0:
            return True

        # === Step 3: Return (speed = dist / delay 자동계산) ===
        if job.y_return_delay > 0:
            return_speed = int(job.y_return_distance / job.y_return_delay * 60)
            if return_speed < 1:
                return_speed = 1
        else:
            return_speed = 600
        return_start = time.monotonic()
        return_dist = -job.y_return_distance
        print(f"[PrintWorker] {label}: Return {job.y_return_distance}mm @ {return_speed}mm/min (delay {job.y_return_delay}s)")
        success, actual_ret = self._motor_y_move(return_dist, return_speed)
        if not success:
            self.error_occurred.emit(f"{label}: Resin return failed")
            self._is_stopped = True
            return False
        self._y_position += actual_ret
        print(f"[PrintWorker] {label}: Return done {actual_ret:.2f}mm (pos: {self._y_position:.1f}mm)")

        # Return delay 남은 시간 대기
        return_remaining = job.y_return_delay - (time.monotonic() - return_start)
        if return_remaining > 0:
            if not self._wait_interruptible(return_remaining):
                return False

        return True

    # ==================== 유틸리티 ====================

    def _run_leveling(self, cycles: int, speed: int):
        """레진 평탄화"""
        print(f"[PrintWorker] 레진 평탄화 ({cycles}회)")

        if self.motor and not self.simulation:
            self.motor.leveling_cycle(cycles, speed)
        else:
            # 시뮬레이션
            for i in range(cycles):
                if self._check_stopped():
                    return
                print(f"[PrintWorker] 평탄화 {i+1}/{cycles}")
                time.sleep(0.5)

    def _wait_exposure(self, duration: float):
        """
        노광 대기 (정지만 체크, 일시정지는 무시)

        노광 중에는 LED가 켜져있으므로 일시정지하면 안 됨.
        노광 완료 후 LED OFF → 일시정지 체크는 _process_layer에서 처리.
        정지 시 즉시 LED OFF 후 return.

        Args:
            duration: 노광 시간 (초)
        """
        start = time.monotonic()

        while (time.monotonic() - start) < duration:
            if self._check_stopped():
                self._dlp_led_off()
                self.clear_image.emit()
                return

            time.sleep(0.1)  # 100ms 간격으로 정지 체크

    def _check_stopped(self) -> bool:
        """정지 여부 확인"""
        self._mutex.lock()
        stopped = self._is_stopped
        self._mutex.unlock()
        return stopped

    def _check_paused(self):
        """일시정지 체크 및 대기 (Klipper pause/resume 연동)"""
        self._mutex.lock()
        if self._is_paused and not self._is_stopped:
            # Klipper에 일시정지 알림 (idle timeout 방지)
            self._mutex.unlock()
            if self.motor and not self.simulation:
                self.motor.klipper_pause()
            self._mutex.lock()

            while self._is_paused and not self._is_stopped:
                self._pause_condition.wait(self._mutex, 1000)

            # 재개 시 Klipper 상태 확인 및 복구
            if not self._is_stopped:
                self._mutex.unlock()
                if self.motor and not self.simulation:
                    self._recover_klipper()
                self._mutex.lock()
        self._mutex.unlock()

    def _recover_klipper(self):
        """Klipper 상태 확인 후 복구 (일시정지 재개 시 호출)"""
        state = self.motor.get_klipper_state()

        if state == "shutdown":
            # idle_timeout으로 shutdown된 경우 → 펌웨어 재시작 + 재홈잉
            print("[PrintWorker] Klipper shutdown 감지 → 복구 시작")
            if not self.motor.firmware_restart():
                print("[PrintWorker] Klipper 재시작 실패")
                self.error_occurred.emit("Klipper 재시작 실패 - 프린터를 재부팅해주세요")
                self._mutex.lock()
                self._is_stopped = True
                self._mutex.unlock()
                return

            # 재홈잉 (shutdown 후 위치 정보 소실)
            print("[PrintWorker] 재홈잉 시작")
            if not self.motor.z_home():
                print("[PrintWorker] Z축 재홈잉 실패")
                self.error_occurred.emit("Z축 재홈잉 실패")
                self._mutex.lock()
                self._is_stopped = True
                self._mutex.unlock()
                return
            if not self.motor.x_home():
                print("[PrintWorker] X축 재홈잉 실패")
                self.error_occurred.emit("X축 재홈잉 실패")
                self._mutex.lock()
                self._is_stopped = True
                self._mutex.unlock()
                return

            print("[PrintWorker] Klipper 복구 완료")
            # CLEAR_PAUSE 후 진행
            self.motor.klipper_clear_pause()
        else:
            # 정상 상태 → RESUME 후 진행
            self.motor.klipper_resume()
            time.sleep(2.0)  # Klipper RESUME 처리 완료 대기

    def _cleanup(self):
        """정리 (STOP 또는 완료 시)"""
        print("[PrintWorker] 정리 중...")

        # LED OFF
        self._dlp_led_off()

        # 프로젝터는 끄지 않음 (앱 실행 동안 계속 ON 유지)

        # 이미지 클리어
        self.clear_image.emit()

        # Z축은 현재 위치 유지 (빌드 플레이트 그대로)
        # X축 홈 복귀
        self._motor_x_home()

        # Klipper 일시정지 상태 초기화 + 프린트 종료 알림
        if self.motor and not self.simulation:
            self.motor.klipper_clear_pause()
            self.motor.klipper_cancel()

        self._set_status(PrintStatus.IDLE)
        print("[PrintWorker] 정리 완료")


# 테스트용
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    worker = PrintWorker()
    worker.simulation = True

    # 시그널 연결
    worker.status_changed.connect(lambda s: print(f"Status: {s}"))
    worker.progress_updated.connect(lambda c, t: print(f"Progress: {c}/{t}"))
    worker.print_completed.connect(lambda: print("Completed!"))

    # 테스트 파라미터
    params = {
        'totalLayer': 10,
        'layerHeight': 0.05,
        'bottomLayerCount': 2,
        'bottomLayerExposureTime': 5.0,
        'normalExposureTime': 2.0,
    }

    worker.start_print("test.zip", params)
    worker.wait()

    print("Done")
