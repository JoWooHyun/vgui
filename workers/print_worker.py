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
    blade_speed: int = 1500
    led_power: int = 440
    leveling_cycles: int = 1
    blade_cycles: int = 1  # 매 레이어 블레이드 왕복 횟수
    blade_mode: str = "roundtrip"  # "roundtrip"(왕복) / "oneway"(편도)


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
                   blade_speed: int = 1500, led_power: int = 440,
                   leveling_cycles: int = 1, blade_cycles: int = 1,
                   blade_mode: str = "roundtrip"):
        """
        프린트 시작

        Args:
            file_path: ZIP 파일 경로
            params: 프린트 파라미터 딕셔너리
            blade_speed: 블레이드 속도 (mm/min)
            led_power: LED 밝기 (91~1023)
            leveling_cycles: 레진 평탄화 횟수
            blade_cycles: 매 레이어 블레이드 왕복 횟수 (1~3)
            blade_mode: 블레이드 모드 ("roundtrip" 또는 "oneway")
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
            led_power=led_power,
            leveling_cycles=leveling_cycles,
            blade_cycles=blade_cycles,
            blade_mode=blade_mode
        )

        # 플래그 초기화
        self._is_paused = False
        self._is_stopped = False

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
        self._set_status(PrintStatus.STOPPING)
        print("[PrintWorker] 정지 요청")

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

        # Z축 홈
        if self._check_stopped():
            return
        if not self._motor_z_home():
            self.error_occurred.emit("Z축 홈 이동 실패")
            self._is_stopped = True
            return

        # X축 홈
        if self._check_stopped():
            return
        if not self._motor_x_home():
            self.error_occurred.emit("X축 홈 이동 실패")
            self._is_stopped = True
            return

        # 2. 레진 평탄화
        if job.leveling_cycles > 0:
            self._set_status(PrintStatus.LEVELING)
            if self._check_stopped():
                return
            self._run_leveling(job.leveling_cycles, job.blade_speed)

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

        Flow (roundtrip 왕복 모드):
        1. Z축 레이어 높이로 이동
        2. X축 왕복 (0→125→0) × N회
        3. 이미지 투영 → LED ON → 노광 → LED OFF
        4. Z축 리프트 → Z축 다음 레이어

        Flow (oneway 편도 모드):
        1. Z축 레이어 높이로 이동
        2. X축 편도 (0→125) × N회
        3. 이미지 투영 → LED ON → 노광 → LED OFF
        4. Z축 리프트 → X축 복귀(125→0) → Z축 다음 레이어

        Returns:
            bool: 성공 시 True, 실패 시 False (이미지 로드 실패 등)
        """
        params = job.params

        # 바닥 레이어 vs 일반 레이어
        is_bottom = layer_idx < params.bottomLayerCount
        if is_bottom:
            exposure_time = params.bottomLayerExposureTime
            lift_height = params.bottomLayerLiftHeight
            lift_speed = params.bottomLayerLiftSpeed
        else:
            exposure_time = params.normalExposureTime
            lift_height = params.normalLayerLiftHeight
            lift_speed = params.normalLayerLiftSpeed

        # Z축 위치 계산
        z_position = (layer_idx + 1) * params.layerHeight

        # 1. Z축 레이어 높이로 이동
        if not self._motor_z_move(z_position):
            self.error_occurred.emit(f"레이어 {layer_idx}: Z축 이동 실패")
            self._is_stopped = True
            return False

        # 2. X축 블레이드 이동 (blade_mode에 따라 분기)
        if job.blade_mode == "oneway":
            # 편도 모드: (0→125) × N회
            for cycle in range(job.blade_cycles):
                if not self._motor_x_move(125, job.blade_speed):
                    self.error_occurred.emit(f"레이어 {layer_idx}: X축 이동 실패")
                    self._is_stopped = True
                    return False
                # N회 반복 시 중간에 홈 복귀 (마지막 제외)
                if cycle < job.blade_cycles - 1:
                    if not self._motor_x_move(0, job.blade_speed):
                        self.error_occurred.emit(f"레이어 {layer_idx}: X축 복귀 실패")
                        self._is_stopped = True
                        return False
        else:
            # 왕복 모드: (0→125→0) × N회
            for cycle in range(job.blade_cycles):
                if not self._motor_x_move(125, job.blade_speed):
                    self.error_occurred.emit(f"레이어 {layer_idx}: X축 이동 실패")
                    self._is_stopped = True
                    return False
                if not self._motor_x_move(0, job.blade_speed):
                    self.error_occurred.emit(f"레이어 {layer_idx}: X축 복귀 실패")
                    self._is_stopped = True
                    return False

        # 정지/일시정지 체크 (LED ON 전에)
        if self._check_stopped():
            return True  # 정지 요청은 정상 종료
        self._check_paused()
        if self._check_stopped():
            return True

        # 3. 이미지 투영 (실패 시 프린트 중지)
        if not self._show_layer_image(job.file_path, layer_idx):
            # 이미지 로드 실패 - 프린트 중지
            self._mutex.lock()
            self._is_stopped = True
            self._mutex.unlock()
            return False

        # 4. LED ON + 노광
        self._dlp_led_on(job.led_power)

        # 노광 대기 (일시정지/정지 체크하면서)
        self._wait_exposure(exposure_time)

        # 5. LED OFF
        self._dlp_led_off()

        # 이미지 클리어
        self.clear_image.emit()

        # LED OFF 후 일시정지/정지 체크
        if self._check_stopped():
            return True
        self._check_paused()
        if self._check_stopped():
            return True

        # 6. Z축 리프트
        if not self._motor_z_move(z_position + lift_height, lift_speed):
            self.error_occurred.emit(f"레이어 {layer_idx}: Z축 리프트 실패")
            self._is_stopped = True
            return False

        # 편도 모드: 리프트 후 X축 복귀 (125→0)
        if job.blade_mode == "oneway":
            if not self._motor_x_move(0, job.blade_speed):
                self.error_occurred.emit(f"레이어 {layer_idx}: X축 복귀 실패")
                self._is_stopped = True
                return False

        # 7. Z축 다음 레이어 높이로 하강 (마지막 레이어가 아닐 때만)
        if layer_idx < job.params.totalLayer - 1:
            next_z = (layer_idx + 2) * params.layerHeight
            if not self._motor_z_move(next_z, params.normalDropSpeed):
                self.error_occurred.emit(f"레이어 {layer_idx}: Z축 하강 실패")
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

    def _motor_x_move(self, position: float, speed: int = 4500) -> bool:
        """X축 이동"""
        if self.motor and not self.simulation:
            return self.motor.x_move_absolute(position, speed)
        else:
            time.sleep(0.2)
            return True

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

        Args:
            duration: 노광 시간 (초)
        """
        elapsed = 0.0
        interval = 0.1  # 100ms 간격으로 체크

        while elapsed < duration:
            if self._check_stopped():
                return

            time.sleep(interval)
            elapsed += interval

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

            # 재개 시 Klipper에 알림
            if not self._is_stopped:
                self._mutex.unlock()
                if self.motor and not self.simulation:
                    self.motor.klipper_resume()
                    time.sleep(2.0)  # Klipper RESUME 처리 완료 대기
                self._mutex.lock()
        self._mutex.unlock()

    def _cleanup(self):
        """정리 (STOP 또는 완료 시)"""
        print("[PrintWorker] 정리 중...")

        # LED OFF
        self._dlp_led_off()

        # 프로젝터는 끄지 않음 (앱 실행 동안 계속 ON 유지)

        # 이미지 클리어
        self.clear_image.emit()

        # X축만 홈 복귀 (Z축은 현재 위치 유지 - 안전을 위해)
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
