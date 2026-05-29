"""
VERICOM DLP 3D Printer - Test Print Worker
DLP 없이 모터만 동작하는 테스트 프린트 워커
LED ON/OFF → 5초 대기로 대체
"""

import time
from enum import Enum, auto
from typing import Optional, Dict, Any
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition

from controllers.motor_controller import MotorController


# LED 대체 대기 시간 (초)
LED_SUBSTITUTE_DELAY = 5.0


class PrintStatus(Enum):
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
    total_layers: int = 100
    layer_height: float = 0.05
    z_offset: float = 0.0
    blade_speed: int = 300       # mm/min (구간1: start→boundary)
    blade_speed2: int = 1200     # mm/min (구간2: boundary→end)
    blade_boundary: float = 60.0 # 구간 경계 위치 (mm)
    blade_start: float = 0.0    # 블레이드 시작 위치 (mm)
    blade_end: float = 130.0    # 블레이드 끝 위치 (mm)
    blade_cycles: int = 1
    leveling_cycles: int = 1
    settle_time: float = 0.0         # 초기+첫레이어 토출 후 대기(초)
    initial_leveling: bool = True    # 초기 평탄화 ON/OFF
    y_dispense_distance: float = 1.0
    y_dispense_speed: int = 300
    y_dispense_delay: float = 2.0
    y_priming_position: float = 0.0
    y_pull_distance: float = 0.0
    y_pull_delay: float = 2.0
    y_return_distance: float = 0.0
    y_return_delay: float = 2.0


class TestPrintWorker(QThread):
    """테스트용 프린트 워커 - DLP 없이 모터만 동작"""

    status_changed = Signal(str)
    progress_updated = Signal(int, int)  # current, total
    layer_started = Signal(int)
    error_occurred = Signal(str)
    print_completed = Signal()
    print_stopped = Signal()
    resin_empty = Signal()

    def __init__(self, motor: Optional[MotorController] = None, parent=None):
        super().__init__(parent)

        self.motor = motor

        self._status = PrintStatus.IDLE
        self._is_paused = False
        self._is_stopped = False

        self._mutex = QMutex()
        self._pause_condition = QWaitCondition()
        self._resin_mutex = QMutex()
        self._resin_condition = QWaitCondition()

        self._y_position = 0.0
        self._y_dispensing_disabled = False
        self._y_resin_waiting = False

        self._job: Optional[PrintJob] = None

        self.simulation = False

    @property
    def status(self) -> PrintStatus:
        return self._status

    def _set_status(self, status: PrintStatus):
        self._status = status
        self.status_changed.emit(status.name)
        print(f"[TestPrintWorker] 상태: {status.name}")

    def start_print(self, params: Dict[str, Any],
                    blade_speed: int = 300,
                    blade_speed2: int = 1200,
                    blade_boundary: float = 60.0,
                    leveling_cycles: int = 1,
                    blade_cycles: int = 1,
                    y_dispense_distance: float = 1.0,
                    y_dispense_speed: int = 300,
                    y_dispense_delay: float = 2.0,
                    y_priming_position: float = 0.0,
                    y_pull_distance: float = 0.0,
                    y_pull_delay: float = 2.0,
                    y_return_distance: float = 0.0,
                    y_return_delay: float = 2.0,
                    initial_leveling: bool = True,
                    blade_start: float = 0.0,
                    blade_end: float = 130.0):
        if self.isRunning():
            print("[TestPrintWorker] 이미 실행 중")
            return

        self._job = PrintJob(
            total_layers=params.get('totalLayer', 100),
            layer_height=params.get('layerHeight', 0.05),
            z_offset=params.get('zOffset', 0.0),
            blade_speed=blade_speed,
            blade_speed2=blade_speed2,
            blade_boundary=blade_boundary,
            blade_start=blade_start,
            blade_end=blade_end,
            blade_cycles=blade_cycles,
            leveling_cycles=leveling_cycles,
            settle_time=params.get('settleTime', 0.0),
            initial_leveling=initial_leveling,
            y_dispense_distance=y_dispense_distance,
            y_dispense_speed=y_dispense_speed,
            y_dispense_delay=y_dispense_delay,
            y_priming_position=y_priming_position,
            y_pull_distance=y_pull_distance,
            y_pull_delay=y_pull_delay,
            y_return_distance=y_return_distance,
            y_return_delay=y_return_delay,
        )

        self._is_paused = False
        self._is_stopped = False
        self._y_position = y_priming_position
        self._y_dispensing_disabled = False
        self._y_resin_waiting = False

        self.start()

    def pause(self):
        self._mutex.lock()
        self._is_paused = True
        self._mutex.unlock()
        self._set_status(PrintStatus.PAUSED)

    def resume(self):
        self._mutex.lock()
        self._is_paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()
        self._set_status(PrintStatus.PRINTING)

    def stop(self):
        self._mutex.lock()
        self._is_stopped = True
        self._is_paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()
        self._resin_mutex.lock()
        self._y_resin_waiting = False
        self._resin_condition.wakeAll()
        self._resin_mutex.unlock()
        self._set_status(PrintStatus.STOPPING)

    def disable_y_dispensing(self):
        self._y_dispensing_disabled = True
        self._resin_mutex.lock()
        self._y_resin_waiting = False
        self._resin_condition.wakeAll()
        self._resin_mutex.unlock()

    def refill_resin(self, new_y_position: float):
        self._y_position = new_y_position
        self._y_dispensing_disabled = False
        self._resin_mutex.lock()
        self._y_resin_waiting = False
        self._resin_condition.wakeAll()
        self._resin_mutex.unlock()
        print(f"[TestPrintWorker] Resin refilled, new Y position: {new_y_position}mm")

    def stop_by_resin_empty(self):
        self._resin_mutex.lock()
        self._y_resin_waiting = False
        self._resin_condition.wakeAll()
        self._resin_mutex.unlock()
        self.stop()

    # ==================== 메인 루프 ====================

    def run(self):
        if not self._job:
            self.error_occurred.emit("프린트 작업이 없습니다")
            return
        try:
            self._run_print_sequence()
        except Exception as e:
            self._set_status(PrintStatus.ERROR)
            self.error_occurred.emit(str(e))
            print(f"[TestPrintWorker] 오류: {e}")
        finally:
            self._cleanup()

    def _run_print_sequence(self):
        job = self._job

        # 1. 초기화
        self._set_status(PrintStatus.INITIALIZING)
        print(f"[TestPrintWorker] 테스트 프린트 시작")
        print(f"  - 총 레이어: {job.total_layers}")
        print(f"  - 블레이드 범위: {job.blade_start}~{job.blade_end} mm")
        print(f"  - 블레이드 속도1: {job.blade_speed} mm/min ({job.blade_start}→{job.blade_boundary}mm)")
        print(f"  - 블레이드 속도2: {job.blade_speed2} mm/min ({job.blade_boundary}→{job.blade_end}mm)")
        if job.y_pull_distance > 0:
            net = job.y_dispense_distance - job.y_pull_distance + job.y_return_distance
            print(f"  - Push-Pull: push {job.y_dispense_distance}mm, pull {job.y_pull_distance}mm, return {job.y_return_distance}mm (net {net:.2f}mm)")

        if not self.simulation:
            if self.motor:
                self.motor.connect()
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

            # Resin 위치
            print(f"[TestPrintWorker] Resin start position: {job.y_priming_position}mm")
            self._y_position = job.y_priming_position

            # 2. 첫 레진 토출
            INITIAL_DISPENSE_SPEED = 180  # mm/min (3mm/s)
            if not self._y_dispensing_disabled and self._y_position > 0:
                if self._check_stopped():
                    return
                if not self._dispense_3step(-1, job, push_speed_override=INITIAL_DISPENSE_SPEED):
                    return

            # Settle time 대기 (초기 토출)
            if job.settle_time > 0:
                print(f"[TestPrintWorker] 초기 토출 settle time: {job.settle_time}초")
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
            if not self._motor_x_move(job.blade_start, 1800):
                self.error_occurred.emit("초기 평탄화 X 복귀 실패")
                self._is_stopped = True
                return
            # Z 홈 복귀
            if not self._motor_z_home():
                self.error_occurred.emit("초기 평탄화 Z 홈 복귀 실패")
                self._is_stopped = True
                return
        else:
            print("[TestPrintWorker] 초기 평탄화 OFF — 스킵")
            self._y_position = job.y_priming_position

        # 4. 메인 프린팅 루프
        self._set_status(PrintStatus.PRINTING)
        total_layers = job.total_layers

        for layer_idx in range(total_layers):
            if self._check_stopped():
                break
            self._check_paused()
            if self._check_stopped():
                break

            self.layer_started.emit(layer_idx)
            self.progress_updated.emit(layer_idx + 1, total_layers)

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
        """레이어 처리 (DLP 없음, LED → 5초 대기)"""
        z_position = job.z_offset + (layer_idx + 1) * job.layer_height

        # 1. Z축 이동
        if not self._motor_z_move(z_position):
            self.error_occurred.emit(f"레이어 {layer_idx}: Z축 이동 실패")
            self._is_stopped = True
            return False

        # 2. Resin 토출
        if job.y_dispense_distance > 0:
            if self._y_dispensing_disabled:
                print(f"[TestPrintWorker] Layer {layer_idx}: Manual feed mode — Y skip, waiting {job.y_dispense_delay}s")
                if not self._wait_interruptible(job.y_dispense_delay):
                    return False
            elif self._y_position <= 0:
                print(f"[TestPrintWorker] Resin empty at {self._y_position}mm")
                self._y_resin_waiting = True
                self.resin_empty.emit()
                self._resin_mutex.lock()
                while self._y_resin_waiting and not self._is_stopped:
                    self._resin_condition.wait(self._resin_mutex, 1000)
                self._resin_mutex.unlock()
                if self._check_stopped():
                    return True
                if self._y_dispensing_disabled:
                    print(f"[TestPrintWorker] Layer {layer_idx}: Manual feed mode — Y skip, waiting {job.y_dispense_delay}s")
                    if not self._wait_interruptible(job.y_dispense_delay):
                        return False
                else:
                    if not self._dispense_3step(layer_idx, job):
                        return False
            else:
                if not self._dispense_3step(layer_idx, job):
                    return False

        # Settle time 대기 (첫 레이어만)
        if layer_idx == 0 and job.settle_time > 0:
            print(f"[TestPrintWorker] Layer 0 settle time: {job.settle_time}초")
            if not self._wait_interruptible(job.settle_time):
                return True

        # 3. X축 평탄화 (2구간)
        if not self._motor_x_move(job.blade_boundary, job.blade_speed):
            self.error_occurred.emit(f"레이어 {layer_idx}: X축 평탄화(구간1) 실패")
            self._is_stopped = True
            return False
        if not self._motor_x_move(job.blade_end, job.blade_speed2):
            self.error_occurred.emit(f"레이어 {layer_idx}: X축 평탄화(구간2) 실패")
            self._is_stopped = True
            return False

        if self._check_stopped():
            return True
        self._check_paused()
        if self._check_stopped():
            return True

        # 4. LED 대체 → 5초 대기
        print(f"[TestPrintWorker] Layer {layer_idx}: LED 대기 {LED_SUBSTITUTE_DELAY}초")
        if not self._wait_interruptible(LED_SUBSTITUTE_DELAY):
            return True

        if self._check_stopped():
            return True
        self._check_paused()
        if self._check_stopped():
            return True

        # 5. Z축 리프트 (+3mm)
        z_lift_position = z_position + 3.0
        if not self._motor_z_move(z_lift_position):
            self.error_occurred.emit(f"레이어 {layer_idx}: Z축 리프트 실패")
            self._is_stopped = True
            return False

        # 6. X축 복귀 (end→start, 30mm/s)
        if not self._motor_x_move(job.blade_start, 1800):
            self.error_occurred.emit(f"레이어 {layer_idx}: X축 복귀 실패")
            self._is_stopped = True
            return False

        return True

    # ==================== 토출 헬퍼 ====================

    def _wait_interruptible(self, seconds: float) -> bool:
        start = time.monotonic()
        while (time.monotonic() - start) < seconds:
            if self._check_stopped():
                return False
            time.sleep(0.1)
        return True

    def _dispense_3step(self, layer_idx: int, job: PrintJob,
                        push_speed_override: int = 0) -> bool:
        """3단계 토출: Push → Delay → Pull → Return"""
        label = "Initial" if layer_idx < 0 else f"Layer {layer_idx}"
        push_speed = push_speed_override if push_speed_override else job.y_dispense_speed

        # Step 1: Push
        push_dist = -job.y_dispense_distance
        success, actual = self._motor_y_move(push_dist, push_speed)
        if not success:
            self.error_occurred.emit(f"{label}: Resin push failed")
            self._is_stopped = True
            return False
        self._y_position += actual
        print(f"[TestPrintWorker] {label}: Push {actual:.2f}mm (pos: {self._y_position:.1f}mm)")

        if self._y_position <= 0:
            print(f"[TestPrintWorker] {label}: Resin exhausted (pos: {self._y_position:.1f}mm), skipping pull/return")
            if not self._wait_interruptible(job.y_dispense_delay):
                return False
            return True

        # Resin Delay
        if job.y_dispense_delay > 0:
            if not self._wait_interruptible(job.y_dispense_delay):
                return False

        if job.y_pull_distance <= 0:
            return True

        # Step 2: Pull
        if job.y_pull_delay > 0:
            pull_speed = int(job.y_pull_distance / job.y_pull_delay * 60)
            if pull_speed < 1:
                pull_speed = 1
        else:
            pull_speed = 600
        pull_start = time.monotonic()
        success, actual_pull = self._motor_y_move(job.y_pull_distance, pull_speed)
        if not success:
            self.error_occurred.emit(f"{label}: Resin pull failed")
            self._is_stopped = True
            return False
        self._y_position += actual_pull

        pull_remaining = job.y_pull_delay - (time.monotonic() - pull_start)
        if pull_remaining > 0:
            if not self._wait_interruptible(pull_remaining):
                return False

        if job.y_return_distance <= 0:
            return True

        # Step 3: Return
        if job.y_return_delay > 0:
            return_speed = int(job.y_return_distance / job.y_return_delay * 60)
            if return_speed < 1:
                return_speed = 1
        else:
            return_speed = 600
        return_start = time.monotonic()
        return_dist = -job.y_return_distance
        success, actual_ret = self._motor_y_move(return_dist, return_speed)
        if not success:
            self.error_occurred.emit(f"{label}: Resin return failed")
            self._is_stopped = True
            return False
        self._y_position += actual_ret

        return_remaining = job.y_return_delay - (time.monotonic() - return_start)
        if return_remaining > 0:
            if not self._wait_interruptible(return_remaining):
                return False

        return True

    # ==================== 모터 래퍼 ====================

    def _motor_z_home(self) -> bool:
        print("[TestPrintWorker] Z축 홈")
        if self.motor and not self.simulation:
            return self.motor.z_home()
        else:
            time.sleep(0.5)
            return True

    def _motor_x_home(self, force: bool = True) -> bool:
        print("[TestPrintWorker] X축 홈")
        if self.motor and not self.simulation:
            return self.motor.x_home(force=force)
        else:
            time.sleep(0.3)
            return True

    def _motor_z_move(self, position: float, speed: int = 300) -> bool:
        if self.motor and not self.simulation:
            return self.motor.z_move_absolute(position, speed)
        else:
            time.sleep(0.1)
            return True

    def _motor_x_move(self, position: float, speed: int = 300) -> bool:
        if self.motor and not self.simulation:
            return self.motor.x_move_absolute(position, speed)
        else:
            time.sleep(0.2)
            return True

    def _motor_y_move(self, distance: float, speed: int = 300) -> tuple:
        if self.motor and not self.simulation:
            before = self.motor._y_position
            success = self.motor.y_move_relative(distance, speed)
            actual = self.motor._y_position - before
            return success, actual
        else:
            time.sleep(0.1)
            return True, distance

    # ==================== 유틸리티 ====================

    def _run_leveling(self, cycles: int, speed: int):
        print(f"[TestPrintWorker] 레진 평탄화 ({cycles}회)")
        if self.motor and not self.simulation:
            self.motor.leveling_cycle(cycles, speed)
        else:
            for i in range(cycles):
                if self._check_stopped():
                    return
                time.sleep(0.5)

    def _check_stopped(self) -> bool:
        self._mutex.lock()
        stopped = self._is_stopped
        self._mutex.unlock()
        return stopped

    def _check_paused(self):
        self._mutex.lock()
        if self._is_paused and not self._is_stopped:
            self._mutex.unlock()
            if self.motor and not self.simulation:
                self.motor.klipper_pause()
            self._mutex.lock()

            while self._is_paused and not self._is_stopped:
                self._pause_condition.wait(self._mutex, 1000)

            if not self._is_stopped:
                self._mutex.unlock()
                if self.motor and not self.simulation:
                    self.motor.klipper_resume()
                    time.sleep(2.0)
                self._mutex.lock()
        self._mutex.unlock()

    def _cleanup(self):
        print("[TestPrintWorker] 정리 중...")
        self._motor_x_home()
        if self.motor and not self.simulation:
            self.motor.klipper_clear_pause()
            self.motor.klipper_cancel()
        self._set_status(PrintStatus.IDLE)
        print("[TestPrintWorker] 정리 완료")
